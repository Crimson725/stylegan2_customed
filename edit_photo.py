import os
import pickle
import shutil

import PIL.Image
import numpy as np

import dnnlib
import dnnlib.tflib as tflib


def read_feature(file_name):
    file = open(file_name, mode='r')
    # 使用readlines() 读取所有行的数据，会返回一个列表，列表中存放的数据就是每一行的内容
    contents = file.readlines()
    # 准备一个列表，用来存放取出来的数据
    code = np.zeros((512,))
    # for循环遍历列表，去除每一行读取到的内容
    for i in range(512):
        name = contents[i]
        name = name.strip('\n')
        code[i] = name
    code = np.float32(code)
    file.close()
    return code


def move_latent_and_save(latent_vector, direction_file, coeffs, Gs_network, Gs_syn_kwargs):
    direction = np.load('latent_directions/' + direction_file)
    os.makedirs('results/' + direction_file.split('.')[0], exist_ok=True)
    '''latent_vector是人脸潜编码，direction是人脸调整方向，coeffs是变化步幅的向量，generator是生成器'''
    for i, coeff in enumerate(coeffs):
        new_latent_vector = latent_vector.copy()
        new_latent_vector[0][:8] = (latent_vector[0] + coeff * direction)[:8]
        images = Gs_network.components.synthesis.run(new_latent_vector, **Gs_syn_kwargs)
        result = PIL.Image.fromarray(images[0], 'RGB')
        result.save('results/' + direction_file.split('.')[0] + '/' + str(i).zfill(3) + '.png')


def edit_image():
    # 选择生成器
    tflib.init_tf()
    with open('networks/generator_yellow-stylegan2-config-f.pkl', "rb") as f:
        generator_network, discriminator_network, Gs_network = pickle.load(f)

    # 这是一些配置参数，不要动它
    w_avg = Gs_network.get_var('dlatent_avg')
    noise_vars = [var for name, var in Gs_network.components.synthesis.vars.items() if name.startswith('noise')]
    Gs_syn_kwargs = dnnlib.EasyDict()
    Gs_syn_kwargs.output_transform = dict(func=tflib.convert_images_to_uint8, nchw_to_nhwc=True)
    Gs_syn_kwargs.randomize_noise = False
    Gs_syn_kwargs.minibatch_size = 1
    truncation_psi = 0.5

    face_latent = read_feature('generate_codes/0000.txt')
    z = np.stack(face_latent for _ in range(1))
    tflib.set_vars({var: np.random.randn(*var.shape.as_list()) for var in noise_vars})  # [height, width]
    w = Gs_network.components.mapping.run(z, None)
    w = w_avg + (w - w_avg) * truncation_psi

    # 在这儿选择调整的方向，共有21种调整方式，它们的名称与分别对应的功能如下所示。
    '''
        age.npy - 调整年龄
        angle_horizontal.npy - 在左右方向上调整人脸角度
        angle_pitch.npy - 在上下方向上调整人脸角度
        beauty.npy - 调整颜值
        emotion_angry.npy - 调整此项可增添/减弱一些生气的情绪（调整步幅建议缩小）
        emotion_disgust.npy - 调整此项可增添/减弱一些厌恶的情绪（调整步幅建议缩小）
        emotion_easy.npy - 调整此项可增添/减弱一些平静的情绪（调整步幅建议缩小）
        emotion_fear.npy - 调整此项可增添/减弱一些害怕的情绪（调整步幅建议缩小）
        emotion_happy.npy - 调整此项可增添/减弱一些开心的情绪（调整步幅建议缩小）
        emotion_sad.npy - 调整此项可增添/减弱一些伤心的情绪（调整步幅建议缩小）
        emotion_surprise.npy - 调整此项可增添/减弱一些惊讶的情绪（调整步幅建议缩小）
        eyes_open.npy - 调整眼睛的闭合程度
        face_shape.npy - 调整脸型
        gender.npy - 调整性别
        glasses.npy - 调整是否戴眼镜
        height.npy - 调整脸的高度
        race_black.npy - 调整此项可接近/远离向黑种人变化
        race_white.npy - 调整此项可接近/远离向白种人变化
        race_yellow.npy - 调整此项可接近/远离向黄种人变化
        smile.npy - 调整笑容
        width.npy - 调整脸的宽度
    '''

    direction_file_list = ['angle_horizontal.npy', 'angle_pitch.npy', 'emotion_angry.npy', 'emotion_disgust.npy',
                           'emotion_easy.npy', 'emotion_fear.npy', 'emotion_happy.npy', 'emotion_sad.npy',
                           'emotion_surprise.npy', 'eyes_open.npy', 'smile.npy']
    # 设置每一种调整将会生成的图片数量
    pic_num = 50
    coeffs = np.linspace(-10, 10, pic_num).tolist()
    for direction_file in direction_file_list:
        # 开始调整并保存图片
        move_latent_and_save(w, direction_file, coeffs, Gs_network, Gs_syn_kwargs)
    i = 0
    # 重命名
    for direction in direction_file_list:
        path = '/results/' + direction.split('.')[0]
        for file in os.listdir(path):
            os.rename(os.path.join(path, file), os.path.join(path, str(i).zfill(5)) + ".png")
            i = i + 1
    # 合并
    all_path = '/generators-with-stylegan2/all_res'
    for root, dirs, files in os.walk('results'):
        for file in files:
            src_file = os.path.join(root, file)
            shutil.copy(src_file, all_path)


if __name__ == "__main__":
    edit_image()