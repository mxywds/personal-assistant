# -*- coding: utf-8 -*-
import json
import os
import random
from abc import ABCMeta, abstractmethod
from uuid import getnode as get_mac

import requests

from robot import logging, config, utils
from robot.sdk import unit

logger = logging.getLogger(__name__)


class AbstractRobot(object):
    __metaclass__ = ABCMeta

    @classmethod
    def get_instance(cls):
        profile = cls.get_config()
        instance = cls(**profile)
        return instance

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def chat(self, texts, parsed):
        pass

    @abstractmethod
    def stream_chat(self, texts):
        pass


class TulingRobot(AbstractRobot):
    SLUG = "tuling"

    def __init__(self, tuling_key):
        """
        图灵机器人
        """
        super(self.__class__, self).__init__()
        self.tuling_key = tuling_key

    @classmethod
    def get_config(cls):
        return config.get("tuling", {})

    def chat(self, texts, parsed=None):
        """
        使用图灵机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        try:
            url = "http://openapi.turingapi.com/openapi/api/v2"
            userid = str(get_mac())[:32]
            body = {
                "perception": {"inputText": {"text": msg}},
                "userInfo": {"apiKey": self.tuling_key, "userId": userid},
            }
            r = requests.post(url, json=body)
            respond = json.loads(r.text)
            result = ""
            if "results" in respond:
                for res in respond["results"]:
                    result += "\n".join(res["values"].values())
            else:
                result = "图灵机器人服务异常，请联系作者"
            logger.info(f"{self.SLUG} 回答：{result}")
            return result
        except Exception:
            logger.critical(
                "Tuling robot failed to response for %r", msg, exc_info=True
            )
            return "抱歉, 图灵机器人服务回答失败"


class UnitRobot(AbstractRobot):
    SLUG = "unit"

    def __init__(self):
        """
        百度UNIT机器人
        """
        super(self.__class__, self).__init__()

    @classmethod
    def get_config(cls):
        return {}

    def chat(self, texts, parsed):
        """
        使用百度UNIT机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        try:
            result = unit.getSay(parsed)
            logger.info("{} 回答：{}".format(self.SLUG, result))
            return result
        except Exception:
            logger.critical("UNIT robot failed to response for %r", msg, exc_info=True)
            return "抱歉, 百度UNIT服务回答失败"


class BingRobot(AbstractRobot):
    SLUG = "bing"

    def __init__(self, prefix, proxy, mode):
        """
        bing
        """
        super(self.__class__, self).__init__()
        self.prefix = prefix
        self.proxy = proxy
        self.mode = mode

    @classmethod
    def get_config(cls):
        return config.get("bing", {})

    def chat(self, texts, parsed):
        """

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        try:
            import asyncio, json
            from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle

            async def query_bing():
                # Passing cookies is "optional"
                bot = await Chatbot.create(proxy=self.proxy)
                m2s = {
                    "creative": ConversationStyle.creative,
                    "balanced": ConversationStyle.balanced,
                    "precise": ConversationStyle.precise
                }
                response = await bot.ask(prompt=self.prefix + "\n" + msg,
                                         conversation_style=m2s[self.mode],
                                         simplify_response=True)
                # print(json.dumps(response, indent=2)) # Returns
                return response["text"]
                await bot.close()

            result = asyncio.run(query_bing())

            logger.info("{} 回答：{}".format(self.SLUG, result))
            return result
        except Exception:
            logger.critical("bing robot failed to response for %r", msg, exc_info=True)
            return "抱歉, bing回答失败"


class AnyQRobot(AbstractRobot):
    SLUG = "anyq"

    def __init__(self, host, port, solr_port, threshold, secondary):
        """
        AnyQ机器人
        """
        super(self.__class__, self).__init__()
        self.host = host
        self.threshold = threshold
        self.port = port
        self.secondary = secondary

    @classmethod
    def get_config(cls):
        # Try to get anyq config from config
        return config.get("anyq", {})

    def chat(self, texts, parsed):
        """
        使用AnyQ机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        try:
            url = f"http://{self.host}:{self.port}/anyq?question={msg}"
            r = requests.get(url)
            respond = json.loads(r.text)
            logger.info(f"anyq response: {respond}")
            if len(respond) > 0:
                # 有命中，进一步判断 confidence 是否达到要求
                confidence = respond[0]["confidence"]
                if confidence >= self.threshold:
                    # 命中该问题，返回回答
                    answer = respond[0]["answer"]
                    if utils.validjson(answer):
                        answer = random.choice(json.loads(answer))
                    logger.info(f"{self.SLUG} 回答：{answer}")
                    return answer
            # 没有命中，走兜底
            if self.secondary != "null" and self.secondary:
                try:
                    ai = get_robot_by_slug(self.secondary)
                    return ai.chat(texts, parsed)
                except Exception:
                    logger.critical(
                        f"Secondary robot {self.secondary} failed to response for {msg}"
                    )
                    return get_unknown_response()
            else:
                return get_unknown_response()
        except Exception:
            logger.critical("AnyQ robot failed to response for %r", msg, exc_info=True)
            return "抱歉, AnyQ回答失败"


class OPENAIRobot(AbstractRobot):
    SLUG = "openai"

    def __init__(
            self,
            openai_api_key,
            model,
            provider,
            api_version,
            temperature,
            max_tokens,
            top_p,
            frequency_penalty,
            presence_penalty,
            stop_ai,
            prefix="",
            proxy="",
            api_base="",
    ):
        """
        OpenAI机器人
        """
        super(self.__class__, self).__init__()
        self.openai = None
        try:
            import openai

            self.openai = openai
            if not openai_api_key:
                openai_api_key = os.getenv("OPENAI_API_KEY")
            self.openai.api_key = openai_api_key
            if proxy:
                logger.info(f"{self.SLUG} 使用代理：{proxy}")
                self.openai.proxy = proxy
            else:
                self.openai.proxy = None

        except Exception:
            logger.critical("OpenAI 初始化失败，请升级 Python 版本至 > 3.6")
        self.model = model
        self.prefix = prefix
        self.provider = provider
        self.api_version = api_version
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.stop_ai = stop_ai
        self.api_base = api_base if api_base else "https://api.openai.com/v1/chat"
        self.context = []

    @classmethod
    def get_config(cls):
        # Try to get anyq config from config
        return config.get("openai", {})

    def stream_chat(self, texts):
        """
        从ChatGPT API获取回复
        :return: 回复
        """

        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        msg = self.prefix + msg  # 增加一段前缀
        logger.info("msg: " + msg)
        self.context.append({"role": "user", "content": msg})

        header = {
            "Content-Type": "application/json",
            # "Authorization": "Bearer " + self.openai.api_key
        }
        if self.provider == 'openai':
            header['Authorization'] = "Bearer " + self.openai.api_key
        elif self.provider == 'azure':
            header['api-key'] = self.openai.api_key
        else:
            raise ValueError("Please check your config file, OpenAiRobot's provider should be openai or azure.")

        data = {"model": self.model, "messages": self.context, "stream": True}
        logger.info(f"使用模型：{self.model}，开始流式请求")
        url = self.api_base + "/completions"
        if self.provider == 'azure':
            url = f"{self.api_base}/openai/deployments/{self.model}/chat/completions?api-version={self.api_version}"
        # 请求接收流式数据
        try:
            response = requests.request(
                "POST",
                url,
                headers=header,
                json=data,
                stream=True,
                proxies={"https": self.openai.proxy},
            )

            def generate():
                stream_content = str()
                one_message = {"role": "assistant", "content": stream_content}
                self.context.append(one_message)
                i = 0
                for line in response.iter_lines():
                    line_str = str(line, encoding="utf-8")
                    if line_str.startswith("data:") and line_str[5:]:
                        if line_str.startswith("data: [DONE]"):
                            break
                        line_json = json.loads(line_str[5:])
                        if "choices" in line_json:
                            if len(line_json["choices"]) > 0:
                                choice = line_json["choices"][0]
                                if "delta" in choice:
                                    delta = choice["delta"]
                                    if "role" in delta:
                                        role = delta["role"]
                                    elif "content" in delta:
                                        delta_content = delta["content"]
                                        i += 1
                                        if i < 40:
                                            logger.debug(delta_content, end="")
                                        elif i == 40:
                                            logger.debug("......")
                                        one_message["content"] = (
                                                one_message["content"] + delta_content
                                        )
                                        yield delta_content

                    elif len(line_str.strip()) > 0:
                        logger.debug(line_str)
                        yield line_str

        except Exception as e:
            ee = e

            def generate():
                yield "request error:\n" + str(ee)

        return generate

    def chat(self, texts, parsed):
        """
        使用OpenAI机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        msg = self.prefix + msg  # 增加一段前缀
        logger.info("msg: " + msg)
        try:
            respond = ""
            self.context.append({"role": "user", "content": msg})
            if self.provider == "openai":
                response = self.openai.Completion.create(
                    model=self.model,
                    messages=self.context,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p,
                    frequency_penalty=self.frequency_penalty,
                    presence_penalty=self.presence_penalty,
                    stop=self.stop_ai,
                    api_base=self.api_base
                )
            else:
                from openai import AzureOpenAI
                client = AzureOpenAI(
                    azure_endpoint=self.api_base,
                    api_key=self.openai_api_key,
                    api_version=self.api_version
                )
                response = client.chat.completions.create(
                    model=self.model,
                    messages=self.context
                )
            message = response.choices[0].message
            respond = message.content
            self.context.append(message)
            return respond
        except self.openai.error.InvalidRequestError:
            logger.warning("token超出长度限制，丢弃历史会话")
            self.context = []
            return self.chat(texts, parsed)
        except Exception:
            logger.critical(
                "openai robot failed to response for %r", msg, exc_info=True
            )
            return "抱歉，OpenAI 回答失败"


class ERNIERobot(AbstractRobot):
    SLUG = "ernie"
    def __init__(
            self,
            api_key,
            secret_key,
            model,
            system,
            temperature,
            max_tokens,
            top_p,
            penalty_score,
            stop_ai,
            disable_search,
            prefix="",
            api_base="",
    ):
        """
        百度ERNIE大语言模型
        """
        super(self.__class__, self).__init__()
        self.openai = None
        self.api_key = api_key
        self.secret_key = secret_key
        self.model = model
        self.prefix = prefix
        self.system = system
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.penalty_score = penalty_score
        self.stop_ai = stop_ai
        self.disable_search = disable_search
        self.api_base = api_base if api_base else "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"
        self.context = []
        url = None
        if self.model == 'ERNIE-4.0-8K':
            url = self.api_base + "/ompletions_pro"
        elif self.model == 'ERNIE-3.5-8K':
            url = self.api_base + "/completions"
        elif self.model == 'ERNIE-Bot-8K':
            url = self.api_base + "/ernie_bot_8k"
        self.url = url+"?access_token=" + self.get_access_token()

    @classmethod
    def get_config(cls):
        # Try to get anyq config from config
        return config.get("ernie", {})

    def stream_chat(self, texts):
        """
        从ERNIE获取回复
        :return: 回复
        """

        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        msg = self.prefix + msg  # 增加一段前缀
        logger.info("msg: " + msg)
        self.context.append({"role": "user", "content": msg})

        header = {"Content-Type": "application/json", 'api-key': self.openai.api_key}
        data = {"model": self.model, "messages": self.context, "stream": True}
        logger.info(f"使用模型：{self.model}，开始流式请求")

        # 请求接收流式数据
        try:
            response = requests.request(
                "POST",
                self.url,
                headers=header,
                json=data,
                stream=True
            )

            def generate():
                stream_content = str()
                one_message = {"role": "assistant", "content": stream_content}
                self.context.append(one_message)
                i = 0
                for line in response.iter_lines():
                    line_str = str(line, encoding="utf-8")
                    if line_str.startswith("data:") and line_str[5:]:
                        if line_str.startswith("data: [DONE]"):
                            break
                        line_json = json.loads(line_str[5:])
                        if "choices" in line_json:
                            if len(line_json["choices"]) > 0:
                                choice = line_json["choices"][0]
                                if "delta" in choice:
                                    delta = choice["delta"]
                                    if "role" in delta:
                                        role = delta["role"]
                                    elif "content" in delta:
                                        delta_content = delta["content"]
                                        i += 1
                                        if i < 40:
                                            logger.debug(delta_content, end="")
                                        elif i == 40:
                                            logger.debug("......")
                                        one_message["content"] = (
                                                one_message["content"] + delta_content
                                        )
                                        yield delta_content

                    elif len(line_str.strip()) > 0:
                        logger.debug(line_str)
                        yield line_str

        except Exception as e:
            ee = e

            def generate():
                yield "request error:\n" + str(ee)

        return generate

    def chat(self, texts, parsed):
        """
        使用ERNIE机器人聊天

        Arguments:
        texts -- user input, typically speech, to be parsed by a module
        """
        msg = "".join(texts)
        msg = utils.stripPunctuation(msg)
        msg = self.prefix + msg  # 增加一段前缀
        logger.info("msg: " + msg)

        try:
            self.context.append({"role": "user", "content": msg})
            payload = json.dumps({
                "messages": self.context,
                "system": self.system,
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
                "top_p": self.top_p,
                "penalty_score": self.penalty_score,
                "stop": self.stop_ai,
                "disable_search": self.disable_search
            })

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", self.url, headers=headers, data=payload)
            message = response.json().get("result")
            self.context.append({"role": "assistant", "content": message})
            return message
        # except :
        #     logger.warning("token超出长度限制，丢弃历史会话")
        #     self.context = []
        #     return self.chat(texts, parsed)
        except Exception:
            logger.critical(
                "ERNIE robot failed to response for %r", msg, exc_info=True
            )
            return "抱歉，ERNIE 回答失败"

    def get_access_token(self):
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": self.api_key, "client_secret": self.secret_key}
        return str(requests.post(url, params=params).json().get("access_token"))


def get_unknown_response():
    """
    不知道怎么回答的情况下的答复

    :returns: 表示不知道的答复
    """
    results = ["抱歉，我不会这个呢", "我不会这个呢", "我还不会这个呢", "我还没学会这个呢", "对不起，你说的这个，我还不会"]
    return random.choice(results)


def get_robot_by_slug(slug):
    """
    Returns:
        A robot implementation available on the current platform
    """
    if not slug or type(slug) is not str:
        raise TypeError("Invalid slug '%s'", slug)

    selected_robots = list(
        filter(
            lambda robot: hasattr(robot, "SLUG") and robot.SLUG == slug, get_robots()
        )
    )
    if len(selected_robots) == 0:
        raise ValueError("No robot found for slug '%s'" % slug)
    else:
        if len(selected_robots) > 1:
            logger.warning(
                "WARNING: Multiple robots found for slug '%s'. "
                + "This is most certainly a bug." % slug
            )
        robot = selected_robots[0]
        logger.info(f"使用 {robot.SLUG} 对话机器人")
        return robot.get_instance()


def get_robots():
    def get_subclasses(cls):
        subclasses = set()
        for subclass in cls.__subclasses__():
            subclasses.add(subclass)
            subclasses.update(get_subclasses(subclass))
        return subclasses

    return [
        robot
        for robot in list(get_subclasses(AbstractRobot))
        if hasattr(robot, "SLUG") and robot.SLUG
    ]