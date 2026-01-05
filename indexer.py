import asyncio
import aiohttp
import time
import hashlib
import urllib.parse
from datetime import datetime
import json
import logging
import re

logger = logging.getLogger(__name__)


class RequestLimiter:
    """请求限制器，控制QPS"""
    def __init__(self, qps=4):
        self.qps = qps
        self.interval = 1.0 / qps
        self.last_request_time = 0
        
    async def acquire(self):
        now = time.time()
        time_passed = now - self.last_request_time
        if time_passed < self.interval:
            await asyncio.sleep(self.interval - time_passed)
        self.last_request_time = time.time()


class VideoIndexer:
    """视频索引器，负责获取UP主的视频列表"""
    
    def __init__(self, session=None, cookie="", qps=4):
        self.session = session
        self.own_session = session is None  # 标记是否拥有自己的session
        self.limiter = RequestLimiter(qps)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://space.bilibili.com/',
            'Cookie': cookie,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }
        
    async def __aenter__(self):
        if self.own_session:
            # 创建支持Brotli的会话
            connector = aiohttp.TCPConnector(
                limit=10,             # 严格限制并发连接数
                ttl_dns_cache=300,    # 缓存 DNS
                use_dns_cache=True,
                force_close=False     # 强制保持长连接 (Keep-Alive)
            )
            self.session = aiohttp.ClientSession(headers=self.headers, connector=connector)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.own_session and self.session:
            await self.session.close()

    async def get_mixin_key(self, session):
        """获取mix密钥用于WBI签名"""
        try:
            # 设置Accept-Encoding为gzip, deflate以避免Brotli编码
            headers = self.headers.copy()
            headers['Accept-Encoding'] = 'gzip, deflate'
            
            logger.info("正在获取WBI密钥...")
            resp = await session.get('https://api.bilibili.com/x/web-interface/nav', headers=headers)
            logger.info(f"获取WBI密钥响应状态: {resp.status}")
            
            # 尝试解析响应
            content = await resp.json()
            logger.debug(f"WBI密钥响应数据: {content}")
            
            if content['code'] == -101:  # 账号未登录
                logger.error("Cookie无效或已过期，请更新Cookie")
                raise Exception("Cookie无效或已过期，请更新Cookie")
            
            if content['code'] != 0:
                logger.error(f"获取WBI密钥失败: {content['message']}")
                raise Exception(f"获取WBI密钥失败: {content['message']}")
            
            img_url = content['data']['wbi_img']['img_url']
            sub_url = content['data']['wbi_img']['sub_url']
            
            logger.info(f"原始img_url: {img_url}")
            logger.info(f"原始sub_url: {sub_url}")
            
            # 提取URL中的参数部分
            img_key = img_url.rsplit('/', 1)[1].split('.')[0]
            sub_key = sub_url.rsplit('/', 1)[1].split('.')[0]
            
            logger.info(f"img_key: {img_key}")
            logger.info(f"sub_key: {sub_key}")
            
            # 生成mix_key - 按照B站实际算法
            mixin_key = img_key + sub_key
            logger.info(f"混合mixin_key: {mixin_key}")
            
            # 根据BAC Document给出的64位偏移量序列
            # [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52]
            char_indices = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52]
            filtered_chars = []
            for i in char_indices:
                if i < len(mixin_key):
                    filtered_chars.append(mixin_key[i])
            
            result_key = ''.join(filtered_chars)[:32]
            logger.info(f"最终mixin_key: {result_key}")
            
            return result_key
        except Exception as e:
            logger.error(f"获取mix密钥失败: {e}")
            raise

    def calculate_sign(self, params, mixin_key):
        """计算WBI签名"""
        logger.info(f"计算WBI签名，原始参数: {params}")
        logger.info(f"mixin_key: {mixin_key}")
        
        # 参数注入：wts应该已经在params中
        
        # 值处理：遍历字典，将所有Value转为字符串并剔除特殊字符
        # 过滤列表：!, *, (, ), '
        special_chars_pattern = r'[!*()\'\x5c]'  # 特殊字符正则表达式：! * ( ) '
        cleaned_params = {}
        
        for k, v in params.items():
            # 转换为字符串并清洗特殊字符
            str_v = str(v)
            cleaned_v = re.sub(special_chars_pattern, '', str_v)
            cleaned_params[k] = cleaned_v
        
        logger.info(f"清洗后的参数: {cleaned_params}")
        
        # 排序编码：对字典按Key升序排列，并使用urllib.parse.quote对Value进行编码
        ordered_params = dict(sorted(cleaned_params.items()))
        logger.info(f"排序后参数: {ordered_params}")
        
        # 字符串拼接：形成k1=v1&k2=v2...&wts=xxx的字符串
        query_parts = []
        for k, v in ordered_params.items():
            # 对value进行URL编码
            encoded_v = urllib.parse.quote(str(v), safe='')
            query_parts.append(f'{k}={encoded_v}')
        
        query_str = '&'.join(query_parts)
        logger.info(f"URL编码后的查询字符串: {query_str}")
        
        # 加盐MD5：在字符串尾部直接追加打乱后的mixin_key，最后生成MD5
        sign_str = query_str + mixin_key
        logger.info(f"签名字符串: {sign_str}")
        
        # 计算MD5
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        logger.info(f"签名结果: {sign}")
        
        return sign

    async def get_videos_by_up_id(self, up_id, start_time=None, end_time=None, max_pages=None, qps=4):
        """
        根据UP主ID获取视频列表
        
        :param up_id: UP主ID
        :param start_time: 开始时间过滤
        :param end_time: 结束时间过滤
        :param max_pages: 最大页数
        :param qps: 每秒请求数
        :return: 视频列表（只包含基本信息，不包含CID）
        """
        if not up_id:
            raise ValueError("UP主ID不能为空")
        
        logger.info(f"开始获取UP主 {up_id} 的视频列表")
        logger.info(f"时间范围: {start_time} 到 {end_time}")
        
        # 检查Cookie是否设置
        if not self.headers['Cookie'] or self.headers['Cookie'] == "":
            logger.error("Cookie未设置，请在配置中填入有效的Cookie")
            return []
        
        all_videos = []
        page = 1
        
        # 创建session
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                # 获取mixin_key
                mixin_key = await self.get_mixin_key(session)
            except Exception as e:
                logger.error(f"无法获取WBI密钥，可能是因为Cookie无效: {e}")
                return []
            
            while True:
                if max_pages and page > max_pages:
                    break
                
                # 计算WBI签名参数
                # 1. 先准备所有基础参数，必须先放入wts
                wts = int(time.time())
                params = {
                    'mid': up_id,
                    'order': 'pubdate',  # 按发布时间排序
                    'order_avoided': '1',
                    'platform': 'web',
                    'pn': page,
                    'ps': 30,
                    'wts': wts  # 必须先放入wts
                }
                
                # 2. 计算签名（此时params已包含wts）
                sign = self.calculate_sign(params, mixin_key)
                params['w_rid'] = sign  # 写入签名
                
                logger.info(f"请求参数: {params}")
                
                # 3. 限制频率并请求
                await self.limiter.acquire()
                
                try:
                    logger.info(f"正在获取第 {page} 页视频列表...")
                    logger.info(f"请求URL: https://api.bilibili.com/x/space/wbi/arc/search?{urllib.parse.urlencode(params)}")
                    
                    resp = await session.get('https://api.bilibili.com/x/space/wbi/arc/search', params=params)
                    logger.info(f"API响应状态: {resp.status}")
                    
                    data = await resp.json()
                    logger.debug(f"API响应数据: {data}")
                    
                    if data['code'] == -101:  # 账号未登录
                        logger.error("API请求失败: 账号未登录，请检查Cookie是否有效")
                        break
                    elif data['code'] == -352:  # 风控校验失败
                        logger.error("API请求失败: 风控校验失败，请降低请求频率或检查Cookie")
                        break
                    elif data['code'] == -3:  # API签名错误
                        logger.error("API请求失败: API签名错误，请检查WBI算法")
                        break
                    elif data['code'] != 0:
                        logger.error(f"API请求失败: {data['message']}")
                        break
                    
                    videos_info = data['data']['list']['vlist']
                    
                    # 如果没有视频了，退出
                    if not videos_info:
                        logger.info("没有更多视频了")
                        break
                    
                    logger.info(f"第 {page} 页获取到 {len(videos_info)} 个视频")
                    
                    # 检查Early Exit条件
                    should_exit = False
                    for video in videos_info:
                        video_timestamp = video['created']
                        video_datetime = datetime.fromtimestamp(video_timestamp)
                        
                        logger.debug(f"视频: {video['bvid']}, 发布时间: {video_datetime}, 标题: {video['title']}")
                        
                        # 如果视频发布时间早于开始时间，则应用Early Exit策略
                        if start_time and video_datetime < start_time:
                            logger.info(f"检测到视频发布于 {video_datetime} 早于开始时间 {start_time}，执行Early Exit")
                            should_exit = True
                            break
                        
                        # 检查是否在时间范围内
                        if (not start_time or video_datetime >= start_time) and \
                           (not end_time or video_datetime <= end_time):
                            # 只添加基本信息，不获取CID（在提取器阶段再获取）
                            all_videos.append({
                                'bvid': video['bvid'],
                                'title': video['title'],
                                'duration': video['length'],  # 视频时长字符串，需要转换
                                'created': video['created'],
                                'created_str': datetime.fromtimestamp(video['created']).strftime('%Y-%m-%d %H:%M:%S'),
                                'play': video['play'],
                                'video_url': f"https://www.bilibili.com/video/{video['bvid']}"
                            })
                    
                    if should_exit:
                        break
                        
                    logger.info(f"累计 {len(all_videos)} 个符合条件的视频")
                    page += 1
                    
                    # 增加延时以避免触发风控
                    await asyncio.sleep(3.0)  # 增加延时
                    
                except Exception as e:
                    logger.error(f"获取第 {page} 页视频列表时出错: {e}")
                    import traceback
                    logger.error(f"详细错误信息: {traceback.format_exc()}")
                    break
        
        logger.info(f"总共获取到 {len(all_videos)} 个符合条件的视频")
        return all_videos

    async def get_cid_by_bvid(self, session, bvid):
        """
        通过BVID获取CID
        """
        try:
            logger.info(f"正在获取视频 {bvid} 的CID...")
            params = {
                'bvid': bvid
            }
            resp = await session.get('https://api.bilibili.com/x/player/pagelist', params=params)
            data = await resp.json()
            
            if data['code'] != 0:
                logger.error(f"获取CID失败: {data['message']}")
                return None
            
            if 'data' not in data or not data['data']:
                logger.error("获取CID返回数据格式错误")
                return None
            
            # 获取第一个视频的CID
            first_video = data['data'][0]
            cid = first_video['cid']
            logger.info(f"获取到视频 {bvid} 的CID: {cid}")
            return cid
        except Exception as e:
            logger.error(f"获取CID时出错: {e}")
            return None

    def _convert_duration_to_seconds(self, duration_str):
        """
        将时长字符串转换为秒数
        :param duration_str: 时长字符串，如 '3:45' 或 '1:23:45'
        :return: 秒数
        """
        parts = duration_str.split(':')
        if len(parts) == 2:  # MM:SS
            minutes, seconds = parts
            return int(minutes) * 60 + int(seconds)
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        else:
            return 0