# -*- coding: utf-8 -*-
# @Author  : 曾智鑫
# @Time    : 2022/4/23 19:24
# @Function:
import os
from generator import generate_images
from edit_photo import edit_image


# 创建目录
os.makedirs('results/', exist_ok=True)
os.makedirs('generate_codes/', exist_ok=True)
# 模型路径
model_path = 'networks/generator_yellow-stylegan2-config-f.pkl'
# 生成数量 一次一张(生成后要删除）
generate_num = 1
# 生成随机人脸图片
generate_images(generate_num, model_path)
# 进行微调
edit_image()
# 下次生成前记得删除 all_res results下的所有文件以及generate_codes

