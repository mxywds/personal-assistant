# -*- coding:utf-8 -*-
import torch
from modelscope import snapshot_download
import torchaudio
from . import ChatTTS
from robot import logging
import tempfile

logger = logging.getLogger(__name__)

from robot import utils

chat = None


def load():
    global chat
    logger.info('Loading chat TTS model...')
    torch._dynamo.config.cache_size_limit = 64
    torch._dynamo.config.suppress_errors = True
    torch.set_float32_matmul_precision('high')
    model_dir = snapshot_download('pzc163/chatTTS')
    chat = ChatTTS.Chat()
    chat.load_models(source='local', local_path=model_dir)


def tts(text,seed,temperature,top_P,top_K,use_decoder):
    global chat
    try:
        r = chat.sample_random_speaker(seed=seed)
        params_infer_code = {
            "spk_emb": r,  # add sampled speaker
            "temperature": temperature,  # using custom temperature
            "top_P": top_P,  # top P decode
            "top_K": top_K,  # top K decode
        }
        wavs = chat.infer(text, use_decoder=use_decoder, params_infer_code=params_infer_code)
        with tempfile.NamedTemporaryFile(mode="w+b", suffix=".mp3", delete=False) as f:
            tmpfile = f.name
            torchaudio.save(tmpfile, torch.from_numpy(wavs[0]), 24000)
        return tmpfile
    except Exception as err:
        logger.error(f"ChatTTS处理失败: {err}", stack_info=True)
