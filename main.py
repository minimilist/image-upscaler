from flask import Flask, render_template, request, send_file
import glob
import os.path as osp
import cv2
import numpy as np
import torch
import RRDBNet_arch as arch
import os

app = Flask(__name__)

image_folder = "images/*"
device = torch.device('cpu')
model_path = 'model/RRDB_ESRGAN_x4.pth'

model = arch.RRDBNet(3, 3, 64, 23, gc=32)
model.load_state_dict(torch.load(model_path), strict=True)
model.eval()
model = model.to(device)


def upscale_image(image_path):
    file_name = osp.splitext(osp.basename(image_path))[0]
    print(f"reading... {file_name}")
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    image = image * 1.0 / 255
    image = torch.from_numpy(np.transpose(image[:, :, [2, 1, 0]], (2, 0, 1))).float()
    img = image.unsqueeze(0)
    img = img.to(device)

    with torch.no_grad():
        output = model(img).data.squeeze().float().cpu().clamp_(0, 1).numpy()
        print(f"done... {file_name}")
    output = np.transpose(output[[2, 1, 0], :, :], (1, 2, 0))
    output = (output * 255.0).round()
    output_path = f'results/{file_name}_rlt.png'
    cv2.imwrite(output_path, output)
    print(f"saving.... {file_name}")
    return output_path


@app.route('/', methods=['GET', 'POST'])
def upload_and_process():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            image_path = f"images/{file.filename}"
            file.save(image_path)
            output_path = upscale_image(image_path)
            return send_file(output_path, as_attachment=True)
    return render_template('upload.html')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
