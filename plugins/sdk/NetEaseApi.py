#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: omi
# @Date:   2014-08-24 21:51:57
"""
网易云音乐 Api
"""
from builtins import int
from builtins import open
from builtins import pow

import os
import json
import time
import hashlib
import base64
import binascii
import platform

from collections import OrderedDict
from Crypto.Cipher import AES
from http.cookiejar import LWPCookieJar
from http.cookiejar import Cookie
import requests
import requests_cache
from robot import logging
log = logging.getLogger(__name__)

# 歌曲榜单地址
TOP_LIST_ALL = {
    0: ["云音乐新歌榜", "3779629"],
    1: ["云音乐热歌榜", "3778678"],
    2: ["网易原创歌曲榜", "2884035"],
    3: ["云音乐飙升榜", "19723756"],
    4: ["云音乐电音榜", "10520166"],
    5: ["UK排行榜周榜", "180106"],
    6: ["美国Billboard周榜", "60198"],
    7: ["KTV嗨榜", "21845217"],
    8: ["iTunes榜", "11641012"],
    9: ["Hit FM Top榜", "120001"],
    10: ["日本Oricon周榜", "60131"],
    11: ["韩国Melon排行榜周榜", "3733003"],
    12: ["韩国Mnet排行榜周榜", "60255"],
    13: ["韩国Melon原声周榜", "46772709"],
    14: ["中国TOP排行榜(港台榜)", "112504"],
    15: ["中国TOP排行榜(内地榜)", "64016"],
    16: ["香港电台中文歌曲龙虎榜", "10169002"],
    17: ["华语金曲榜", "4395559"],
    18: ["中国嘻哈榜", "1899724"],
    19: ["法国 NRJ EuroHot 30周榜", "27135204"],
    20: ["台湾Hito排行榜", "112463"],
    21: ["Beatport全球电子舞曲榜", "3812895"],
    22: ["云音乐ACG音乐榜", "71385702"],
    23: ["云音乐嘻哈榜", "991319590"],
}


PLAYLIST_CLASSES = OrderedDict(
    [
        ("语种", ["华语", "欧美", "日语", "韩语", "粤语", "小语种"]),
        (
            "风格",
            [
                "流行",
                "摇滚",
                "民谣",
                "电子",
                "舞曲",
                "说唱",
                "轻音乐",
                "爵士",
                "乡村",
                "R&B/Soul",
                "古典",
                "民族",
                "英伦",
                "金属",
                "朋克",
                "蓝调",
                "雷鬼",
                "世界音乐",
                "拉丁",
                "另类/独立",
                "New Age",
                "古风",
                "后摇",
                "Bossa Nova",
            ],
        ),
        (
            "场景",
            ["清晨", "夜晚", "学习", "工作", "午休", "下午茶", "地铁", "驾车", "运动", "旅行", "散步", "酒吧"],
        ),
        (
            "情感",
            [
                "怀旧",
                "清新",
                "浪漫",
                "性感",
                "伤感",
                "治愈",
                "放松",
                "孤独",
                "感动",
                "兴奋",
                "快乐",
                "安静",
                "思念",
            ],
        ),
        (
            "主题",
            [
                "影视原声",
                "ACG",
                "儿童",
                "校园",
                "游戏",
                "70后",
                "80后",
                "90后",
                "网络歌曲",
                "KTV",
                "经典",
                "翻唱",
                "吉他",
                "钢琴",
                "器乐",
                "榜单",
                "00后",
            ],
        ),
    ]
)

DEFAULT_TIMEOUT = 10

BASE_URL = "http://music.163.com"

MODULUS = (
    "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7"
    "b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280"
    "104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932"
    "575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b"
    "3ece0462db0a22b8e7"
)
PUBKEY = "010001"
NONCE = b"0CoJUm6Qyw8W8jud"


class Parse(object):
    @classmethod
    def _song_url_by_id(cls, sid):
        # 128k
        url = "http://music.163.com/song/media/outer/url?id={}.mp3".format(sid)
        quality = "LD 128k"
        return url, quality

    @classmethod
    def song_url(cls, song):
        if "url" in song:
            # songs_url resp
            url = song["url"]
            if url is None:
                return Parse._song_url_by_id(song["id"])
            br = song["br"]
            if br >= 320000:
                quality = "HD"
            elif br >= 192000:
                quality = "MD"
            else:
                quality = "LD"
            return url, "{} {}k".format(quality, br // 1000)
        else:
            # songs_detail resp
            return Parse._song_url_by_id(song["id"])

    @classmethod
    def song_album(cls, song):
        # 对新老接口进行处理
        if "al" in song and type(song['al']) == list:
            album_name = ", ".join([a["name"] for a in song["al"] if a["name"] is not None])
            album_id = ", ".join(str(a["id"]) for a in song["al"] if a["id"] is not None)
            if album_name == "":
                album_name = "未知专辑"
                album_id = ""
        elif "al" in song:
            if song["al"] is not None:
                album_name = song["al"]["name"]
                album_id = song["al"]["id"]
            else:
                album_name = "未知专辑"
                album_id = ""
        elif "album" in song:
            if song["album"] is not None:
                album_name = song["album"]["name"]
                album_id = song["album"]["id"]
            else:
                album_name = "未知专辑"
                album_id = ""
        elif 'songInfo' in song:
            if song['songInfo']["al"] is not None:
                album_name = song['songInfo']["al"]["name"]
                album_id = song['songInfo']["al"]["id"]
            else:
                album_name = "未知专辑"
                album_id = ""
        elif 'song' in song:
            if song['song']["album"] is not None:
                album_name = song['song']["album"]["name"]
                album_id = song['song']["album"]["id"]
            else:
                album_name = "未知专辑"
                album_id = ""
        else:
            raise ValueError
        return album_name, album_id

    @classmethod
    def song_artist(cls, song):
        artist = ""
        # 对新老接口进行处理
        if "ar" in song:
            artist = ", ".join([a["name"] for a in song["ar"] if a["name"] is not None])
            # 某些云盘的音乐会出现 'ar' 的 'name' 为 None 的情况
            # 不过会多个 ’pc' 的字段
            # {'name': '简单爱', 'id': 31393663, 'pst': 0, 't': 1, 'ar': [{'id': 0, 'name': None, 'tns': [], 'alias': []}],
            #  'alia': [], 'pop': 0.0, 'st': 0, 'rt': None, 'fee': 0, 'v': 5, 'crbt': None, 'cf': None,
            #  'al': {'id': 0, 'name': None, 'picUrl': None, 'tns': [], 'pic': 0}, 'dt': 273000, 'h': None, 'm': None,
            #  'l': {'br': 193000, 'fid': 0, 'size': 6559659, 'vd': 0.0}, 'a': None, 'cd': None, 'no': 0, 'rtUrl': None,
            #  'ftype': 0, 'rtUrls': [], 'djId': 0, 'copyright': 0, 's_id': 0, 'rtype': 0, 'rurl': None, 'mst': 9,
            #  'cp': 0, 'mv': 0, 'publishTime': 0,
            #  'pc': {'nickname': '', 'br': 192, 'fn': '简单爱.mp3', 'cid': '', 'uid': 41533322, 'alb': 'The One 演唱会',
            #         'sn': '简单爱', 'version': 2, 'ar': '周杰伦'}, 'url': None, 'br': 0}
            if artist == "" and "pc" in song:
                artist = "未知艺术家" if song["pc"]["ar"] is None else song["pc"]["ar"]
        elif "artists" in song:
            artist = ", ".join([a["name"] for a in song["artists"]])
        elif "songInfo" in song:
            artist = ", ".join([a["name"] for a in song['songInfo']["ar"] if a["name"] is not None])
        elif "song" in song:
            artist = ", ".join([a["name"] for a in song['song']["artists"]])
        else:
            artist = "未知艺术家"

        return artist

    @classmethod
    def songs(cls, songs):
        song_info_list = []
        for song in songs:
            url, quality = Parse.song_url(song)
            if not url:
                continue

            album_name, album_id = Parse.song_album(song)
            song_info = {
                "song_id": song["id"],
                "artist": Parse.song_artist(song),
                "song_name": song['name'] if 'name' in song else song['songInfo']['name'],
                "album_name": album_name,
                "album_id": album_id,
                "mp3_url": url,
                "quality": quality,
                "expires": song["expires"],
                "get_time": song["get_time"],
            }
            song_info_list.append(song_info)
        return song_info_list

    @classmethod
    def artists(cls, artists):
        return [
            {
                "artist_id": artist["id"],
                "artists_name": artist["name"],
                "alias": "".join(artist["alias"]),
            }
            for artist in artists
        ]

    @classmethod
    def albums(cls, albums):
        return [
            {
                "album_id": album["id"],
                "albums_name": album["name"],
                "artists_name": album["artist"]["name"],
            }
            for album in albums
        ]

    @classmethod
    def playlists(cls, playlists):
        return [
            {
                "playlist_id": pl["id"],
                "playlist_name": pl["name"],
                "creator_name": pl["creator"]["nickname"],
            }
            for pl in playlists
        ]

    @classmethod
    def personalized_playlists(cls, playlists):
        return [
            {
                "playlist_id": pl["id"],
                "playlist_name": pl["name"]
            }
            for pl in playlists
        ]

# 歌曲加密算法, 基于https://github.com/yanunon/NeteaseCloudMusic脚本实现
def encrypted_id(id):
    magic = bytearray('3go8&$8*3*3h0k(2)2', 'u8')
    song_id = bytearray(id, 'u8')
    magic_len = len(magic)
    for i, sid in enumerate(song_id):
        song_id[i] = sid ^ magic[i % magic_len]
    m = hashlib.md5(song_id)
    result = m.digest()
    result = base64.b64encode(result)
    result = result.replace(b'/', b'_')
    result = result.replace(b'+', b'-')
    return result.decode('utf-8')

# 登录加密算法, 基于https://github.com/stkevintan/nw_musicbox脚本实现
def encrypted_request(text):
    text = json.dumps(text).encode('utf-8') ##因为pycryto很久没更新，所以需要编码成utf-8才行
    log.debug(text)
    secKey = createSecretKey(16)
    encText = aesEncrypt(aesEncrypt(text, NONCE), secKey)
    encSecKey = rsaEncrypt(secKey, PUBKEY, MODULUS)
    data = {'params': encText, 'encSecKey': encSecKey}
    return data

def aesEncrypt(text, secKey):
    pad = 16 - len(text) % 16
    text = text + bytearray([pad] * pad)
    encryptor = AES.new(secKey, 2, b'0102030405060708')
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext)
    return ciphertext

def rsaEncrypt(text, pubKey, modulus):
    text = text[::-1]
    rs = pow(int(binascii.hexlify(text), 16), int(pubKey, 16), int(modulus, 16))
    return format(rs, 'x').zfill(256)

def createSecretKey(size):
    return binascii.hexlify(os.urandom(size))[:16]

class NetEase(object):
    def __init__(self):
        self.header = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/search/',
            'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'  # NOQA
        }
        self.cookies = {'appver': '1.5.2'}
        self.playlist_class_dict = {}
        self.session = requests.Session()
        self.check_file(os.path.expanduser("~/.neteasemusic/cookies"), isCookies=True)
        self.check_file(os.path.expanduser("~/.neteasemusic/reqcache"), isCookies=False)
        requests_cache.install_cache(os.path.expanduser("~/.neteasemusic/reqcache"), expire_after=3600)
        self.session.cookies = LWPCookieJar(os.path.expanduser("~/.neteasemusic/cookies"))
        self.session.cookies.load()
        for cookie in self.session.cookies:
            if cookie.is_expired():
                self.session.cookies.clear()

    def check_file(self, path, default="#LWP-Cookies-2.0\n", isCookies=False):
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(default) if isCookies else f.write('')

    @property
    def toplists(self):
        return [l[0] for l in TOP_LIST_ALL.values()]

    def logout(self):
        self.session.cookies.clear()
        self.session.cookies.save()

    def _raw_request(self, method, endpoint, data=None):
        if method == "GET":
            resp = self.session.get(
                endpoint, params=data, headers=self.header, timeout=DEFAULT_TIMEOUT
            )
        elif method == "POST":
            resp = self.session.post(
                endpoint, data=data, headers=self.header, timeout=DEFAULT_TIMEOUT
            )
        return resp

    # 生成Cookie对象
    def make_cookie(self, name, value):
        return Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain="music.163.com",
            domain_specified=True,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=False,
            comment=None,
            comment_url=None,
            rest={},
        )

    def request(self, method, path, params={}, default={"code": -1}, custom_cookies={'os':'pc'}):
        endpoint = "{}{}".format(BASE_URL, path)
        csrf_token = ""
        for cookie in self.session.cookies:
            if cookie.name == "__csrf":
                csrf_token = cookie.value
                break
        params.update({"csrf_token": csrf_token})
        data = default

        for key, value in custom_cookies.items():
            cookie = self.make_cookie(key, value)
            self.session.cookies.set_cookie(cookie)

        params = encrypted_request(params)
        try:
            resp = self._raw_request(method, endpoint, params)
            data = resp.json()
        except requests.exceptions.RequestException as e:
            log.error(e)
        except ValueError as e:
            log.error("Error: {}, Path: {}, response: {}".format(e, path, resp.text[:200]))
        finally:
            return data

    def login(self, username, password):
        self.session.cookies.load()
        if username.isdigit():
            path = "/weapi/login/cellphone"
            params = dict(phone=username, password=password, rememberLogin="true")
        else:
            # magic token for login
            # see https://github.com/Binaryify/NeteaseCloudMusicApi/blob/master/router/login.js#L15
            client_token = (
                "1_jVUMqWEPke0/1/Vu56xCmJpo5vP1grjn_SOVVDzOc78w8OKLVZ2JH7IfkjSXqgfmh"
            )
            path = "/weapi/login"
            params = dict(
                username=username,
                password=password,
                rememberLogin="true",
                clientToken=client_token,
            )
        data = self.request("POST", path, params)
        self.session.cookies.save()
        return data

    # 每日签到
    def daily_task(self, is_mobile=True):
        path = "/weapi/point/dailyTask"
        params = dict(type=0 if is_mobile else 1)
        return self.request("POST", path, params)

    # 用户歌单
    def user_playlist(self, uid, offset=0, limit=50):
        path = "/weapi/user/playlist"
        params = dict(uid=uid, offset=offset, limit=limit, csrf_token="")
        return self.request("POST", path, params).get("playlist", [])

    # 个性化的用户新歌单
    def personalized_playlist(self, total=True, offset=0, limit=30):
        path = "/weapi/personalized/playlist"  # NOQA
        params = dict(total=total, offset=offset, limit=limit, n=1000, csrf_token="")
        return self.request("POST", path, params).get("result", [])

    # 个性化的用户新歌
    def personalized_newsong(self, total=True, offset=0, limit=25):
        path = "/weapi/personalized/newsong"  # NOQA
        params = dict(type='recommend', total=total, offset=offset, limit=limit, csrf_token="")
        return self.request("POST", path, params).get("result", [])

    # 每日推荐歌单
    def recommend_resource(self):
        path = "/weapi/v1/discovery/recommend/resource"
        return self.request("POST", path).get("recommend", [])

    # 每日推荐歌曲
    def recommend_songs(self, total=True, offset=0, limit=20):
        path = "/weapi/v1/discovery/recommend/songs"  # NOQA
        params = dict(total=total, offset=offset, limit=limit, csrf_token="")
        return self.request("POST", path, params).get("recommend", [])

    # 获得相似歌单
    def similar_playlist(self, songid, total=True,offset=0, limit=50):
        path = "/weapi/discovery/simiPlaylist"
        params = dict(songid=songid, total=total, offset=offset, limit=limit, csrf_token="")
        return self.request("POST", path, params)

    # 获得相似歌曲
    def similar_song(self, songid, total=True,offset=0, limit=50):
        path = "/weapi/v1/discovery/simiSong"
        params = dict(songid=songid, total=total, offset=offset, limit=limit, csrf_token="")
        return self.request("POST", path, params)

    # 私人FM
    def personal_fm(self):
        path = "/weapi/v1/radio/get"
        return self.request("POST", path).get("data", [])

    # 用户喜欢（红心）的列表
    def like_playlist(self, uid):
        path = "/weapi/song/like/get"
        params = dict(uid=uid, csrf_token="")
        return self.request("POST", path, params).get("ids", [])

    # 开启心动播放
    def playmode_intelligence(self, sid, pid, type='fromPlayOne', count=1):
        path = "/weapi/playmode/intelligence/list"
        params = dict(songId=sid, type='fromPlayOne', playlistId=pid, startMusicId=sid, count=count, csrf_token="")
        return self.request("POST", path, params).get("data", [])

    # like
    def like_song(self, songid, like=True, time=25, alg="itembased"):
        path = "/weapi/radio/like"
        params = dict(
            alg=alg, trackId=songid, like="true" if like else "false", time=time
        )
        return self.request("POST", path, params)["code"] == 200

   # 收藏歌单
    def subscribe_playlist(self, playlist_id, subscribe=True):
        path = 'weapi/playlist/subscribe'
        params = dict(id=playlist_id, t="true" if subscribe else "false")
        return self.request("POST", path, params)["code"] == 200

    # FM trash
    def fm_trash(self, songid, time=25, alg="RT"):
        path = "/weapi/radio/trash/add"
        params = dict(songId=songid, alg=alg, time=time)
        return self.request("POST", path, params)["code"] == 200

    # 搜索单曲(1)，歌手(100)，专辑(10)，歌单(1000)，用户(1002) *(type)*
    def search(self, keywords, stype=1, offset=0, total="true", limit=50):
        path = "/weapi/search/get"
        params = dict(s=keywords, type=stype, offset=offset, total=total, limit=limit)
        return self.request("POST", path, params).get("result", {})

    # 新碟上架
    def new_albums(self, offset=0, limit=50):
        path = "/weapi/album/new"
        params = dict(area="ALL", offset=offset, total=True, limit=limit)
        return self.request("POST", path, params).get("albums", [])

    # 歌单（网友精选碟） 选风格！！！  hot||new http://music.163.com/#/discover/playlist/
    def top_playlists(self, category="全部", order="hot", offset=0, limit=50):
        path = "/weapi/playlist/list"
        params = dict(
            cat=category, order=order, offset=offset, total="true", limit=limit
        )
        return self.request("POST", path, params).get("playlists", [])

    def playlist_catelogs(self):
        path = "/weapi/playlist/catalogue"
        return self.request("POST", path)

    # 歌单详情
    def playlist_detail(self, playlist_id):
        path = "/weapi/v3/playlist/detail"
        params = dict(id=playlist_id, total="true", limit=1000, n=1000, offest=0)
        # cookie添加os字段
        custom_cookies = dict(os=platform.system())
        return (
            self.request("POST", path, params, {"code": -1}, custom_cookies)
            .get("playlist", {})
            .get("tracks", [])
        )

    # 热门歌手 http://music.163.com/#/discover/artist/
    def top_artists(self, offset=0, limit=100):
        path = "/weapi/artist/top"
        params = dict(offset=offset, total=True, limit=limit)
        return self.request("POST", path, params).get("artists", [])

    # 热门单曲 http://music.163.com/discover/toplist?id=
    def top_songlist(self, idx=0, offset=0, limit=100):
        playlist_id = TOP_LIST_ALL[idx][1]
        return self.playlist_detail(playlist_id)

    # 歌手单曲
    def artists(self, artist_id):
        path = "/weapi/v1/artist/{}".format(artist_id)
        return self.request("POST", path).get("hotSongs", [])

    def get_artist_album(self, artist_id, offset=0, limit=50):
        path = "/weapi/artist/albums/{}".format(artist_id)
        params = dict(offset=offset, total=True, limit=limit)
        return self.request("POST", path, params).get("hotAlbums", [])

    # 用户数字专辑
    def purchased_albums(self, offset=0, limit=50):
        path = "/api/digitalAlbum/purchased"
        params = dict(offset=offset, total=True, limit=limit)
        return self.request("POST", path, params).get("paidAlbums", [])

    # 最新专辑
    def latest_albums(self):
        path = "/api/discovery/newAlbum"
        return self.request("POST", path).get('albums', [])

    # album id --> song id set
    def album(self, album_id):
        path = "/weapi/v1/album/{}".format(album_id)
        return self.request("POST", path).get("songs", [])

    def song_comments(self, music_id, offset=0, total="false", limit=100):
        path = "/weapi/v1/resource/comments/R_SO_4_{}/".format(music_id)
        params = dict(rid=music_id, offset=offset, total=total, limit=limit)
        return self.request("POST", path, params)

    # song ids --> song urls ( details )
    def songs_detail(self, ids):
        path = "/weapi/v3/song/detail"
        params = dict(c=json.dumps([{"id": _id} for _id in ids]), ids=json.dumps(ids))
        return self.request("POST", path, params).get("songs", [])

    def songs_url(self, ids):
        rate_map = {0: 320000, 1: 192000, 2: 128000}

        path = "/weapi/song/enhance/player/url"
        params = dict(ids=ids, br=rate_map[0])
        return self.request("POST", path, params).get("data", [])

    # lyric http://music.163.com/api/song/lyric?os=osx&id= &lv=-1&kv=-1&tv=-1
    def song_lyric(self, music_id):
        path = "/weapi/song/lyric"
        params = dict(os="osx", id=music_id, lv=-1, kv=-1, tv=-1)
        lyric = self.request("POST", path, params).get("lrc", {}).get("lyric", [])
        if not lyric:
            return []
        else:
            return lyric.split("\n")

    def song_tlyric(self, music_id):
        path = "/weapi/song/lyric"
        params = dict(os="osx", id=music_id, lv=-1, kv=-1, tv=-1)
        lyric = self.request("POST", path, params).get("tlyric", {}).get("lyric", [])
        if not lyric:
            return []
        else:
            return lyric.split("\n")

    # 今日最热（0）, 本周最热（10），历史最热（20），最新节目（30）
    def djchannels(self, offset=0, limit=50):
        path = "/weapi/djradio/hot/v1"
        params = dict(limit=limit, offset=offset)
        channels = self.request("POST", path, params).get("djRadios", [])
        return channels

    def djprograms(self, radio_id, asc=False, offset=0, limit=50):
        path = "/weapi/dj/program/byradio"
        params = dict(asc=asc, radioId=radio_id, offset=offset, limit=limit)
        programs = self.request("POST", path, params).get("programs", [])
        return [p["mainSong"] for p in programs]


    def dig_info(self, data, dig_type):
        if not data:
            return []
        if dig_type == "songs" or dig_type == "fmsongs":
            urls = self.songs_url([s["id"] for s in data])
            timestamp = time.time()
            # api 返回的 urls 的 id 顺序和 data 的 id 顺序不一致
            # 为了获取到对应 id 的 url，对返回的 urls 做一个 id2index 的缓存
            # 同时保证 data 的 id 顺序不变
            url_id_index = {}
            for index, url in enumerate(urls):
                url_id_index[url["id"]] = index
            for s in data:
                url_index = url_id_index.get(s["id"])
                if url_index is None:
                    log.error("can't get song url, id: %s", s["id"])
                    continue
                s["url"] = urls[url_index]["url"]
                s["br"] = urls[url_index]["br"]
                s["expires"] = urls[url_index]["expi"]
                s["get_time"] = timestamp
            return Parse.songs(data)

        elif dig_type == "likesongs":
            urls = self.songs_url(data)
            timestamp = time.time()
            infos = self.songs_detail(data)

            url_id_index = {}
            for index, info in enumerate(infos):
                url_id_index[info["id"]] = index

            for s in urls:
                url_index = url_id_index.get(s["id"])
                if url_index is None:
                    log.error("can't get song info, id: %s", s["id"])
                    continue
                s['name'] = infos[url_index]["name"]
                s['ar'] = infos[url_index]["ar"]
                s['al'] = infos[url_index]["ar"]
                s['expires'] = s.pop('expi')
                s['get_time'] = timestamp
            return Parse.songs(urls)

        elif dig_type == "refresh_urls":
            urls_info = self.songs_url(data)
            timestamp = time.time()

            songs = []
            for url_info in urls_info:
                song = {}
                song["song_id"] = url_info["id"]
                song["mp3_url"] = url_info["url"]
                song["expires"] = url_info["expi"]
                song["get_time"] = timestamp
                songs.append(song)
            return songs

        elif dig_type == "artists":
            return Parse.artists(data)

        elif dig_type == "albums":
            return Parse.albums(data)

        elif dig_type == "playlists" or dig_type == "top_playlists":
            return Parse.playlists(data)

        elif dig_type == 'personalized_playlists':
            return Parse.personalized_playlists(data)

        elif dig_type == "playlist_classes":
            return list(PLAYLIST_CLASSES.keys())

        elif dig_type == "playlist_class_detail":
            return PLAYLIST_CLASSES[data]
        else:
            raise ValueError("Invalid dig type")
