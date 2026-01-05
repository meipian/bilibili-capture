import asyncio
import aiohttp
import logging
import bisect
import json
import os
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

class ThumbnailExtractor:
    """缩略图提取器：具备物理像素自动校准与高保真裁剪功能"""
    
    def __init__(self, session, cookie=""):
        self.session = session
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Cookie': cookie
        }
        
    async def fetch_json(self, url, params):
        try:
            async with self.session.get(url, params=params, headers=self.headers, timeout=10) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
        except Exception as e:
            logger.error(f"网络请求异常: {e}")
            return None

    async def get_cid_by_bvid(self, bvid):
        data = await self.fetch_json('https://api.bilibili.com/x/player/pagelist', {'bvid': bvid})
        if data and data.get('code') == 0 and data.get('data'):
            return data['data'][0]['cid']
        return None

    def _parse_pv_data(self, data):
        pv = data.get('pvdata')
        if isinstance(pv, str):
            try:
                pv = json.loads(pv)
            except:
                pv = None
        return pv if isinstance(pv, dict) else data

    async def extract_thumbnail_at_time(self, bvid, time_in_seconds, output_path):
        cid = await self.get_cid_by_bvid(bvid)
        if not cid:
            return False
            
        try:
            params = {'bvid': bvid, 'cid': cid, 'index': 1}
            resp_data = await self.fetch_json('https://api.bilibili.com/x/player/videoshot', params)
            
            if not resp_data or resp_data.get('code') != 0:
                return False

            root_data = resp_data.get('data', {})
            pv = self._parse_pv_data(root_data)

            # 1. 提取元数据（逻辑尺寸）
            img_w = int(pv.get('img_x_len') or pv.get('img_width') or 0)
            img_h = int(pv.get('img_y_len') or pv.get('img_height') or 0)
            img_x_cnt = int(pv.get('img_x_count') or 10)
            img_y_cnt = int(pv.get('img_y_count') or 10)
            images = pv.get('image') or pv.get('images')
            index_list = pv.get('index')

            if not (img_w and img_h and images and index_list):
                logger.error(f"视频 {bvid} 元数据校验失败")
                return False

            # 2. 定位索引
            target_idx = bisect.bisect_right(index_list, time_in_seconds) - 1
            target_idx = max(0, target_idx)

            # 3. 计算逻辑坐标
            pics_per_sheet = img_x_cnt * img_y_cnt
            sheet_index = min(target_idx // pics_per_sheet, len(images) - 1)
            inner_index = target_idx % pics_per_sheet
            
            logic_x = (inner_index % img_x_cnt) * img_w
            logic_y = (inner_index // img_x_cnt) * img_h

            # 4. 下载瓦片图并自动校准像素
            tile_url = images[sheet_index]
            if not tile_url.startswith('http'): 
                tile_url = 'https:' + tile_url
            
            async with self.session.get(tile_url, headers=self.headers) as tile_resp:
                if tile_resp.status != 200:
                    return False
                img_data = await tile_resp.read()
                
                with Image.open(BytesIO(img_data)) as tile_img:
                    real_w, real_h = tile_img.size
                    
                    # 校准系数：部分高清 WebP 瓦片图的物理像素是 API 声明的 2 倍或更多
                    # 我们通过总宽度除以列数，重新计算实际每一格的物理像素宽度
                    scale_w = real_w / (img_w * img_x_cnt)
                    scale_h = real_h / (img_h * img_y_cnt)
                    
                    # 计算物理裁剪坐标
                    phys_x = int(logic_x * scale_w)
                    phys_y = int(logic_y * scale_h)
                    phys_w = int(img_w * scale_w)
                    phys_h = int(img_h * scale_h)

                    # 裁剪并安全转换
                    crop_box = (phys_x, phys_y, phys_x + phys_w, phys_y + phys_h)
                    thumbnail = tile_img.crop(crop_box)
                    
                    if thumbnail.mode != "RGB":
                        thumbnail = thumbnail.convert("RGB")
                    
                    # 5. 保存并质量审计
                    save_ext = os.path.splitext(output_path)[1].lower()
                    save_fmt = 'WEBP' if save_ext == '.webp' else 'JPEG'
                    
                    thumbnail.save(output_path, format=save_fmt, quality=95)
                    
                    size = os.path.getsize(output_path)
                    if size < 500:
                        logger.error(f"异常：{bvid} 裁剪出的图片过小({size}B)，坐标: {crop_box}, 大图尺寸: {tile_img.size}")
                        return False
                    
                    logger.info(f"成功保存: {output_path} ({size} 字节)")
                    return True

        except Exception as e:
            logger.error(f"处理 {bvid} 异常: {e}", exc_info=True)
            return False