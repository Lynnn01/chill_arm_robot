import io
import os
import requests
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# fl-2 api
api_point = "https://llm.educg.com/svc/m4O16tdd-1/object_detect"


def get_objects_coord(img_path, objects):
    data = {
        'objects': objects,
    }
    file = {'image': open(img_path, 'rb')}
    response = requests.post(api_point, data=data, files=file)
    return response.json()


# def get_center_coord(bboxes):
#     x_, y_ = [], []
#     for bbox in bboxes:
#         x1, y1, x2, y2 = bbox
#         x_center = x1 + (x2-x1) / 2
#         y_center = y1 + (y2-y1) / 2
#         x_.append(x_center)
#         y_.append(y_center)
#     return x_, y_
def get_center_coord(bbox):
    x1, y1, x2, y2 = bbox
    x_center = x1 + (x2 - x1) / 2
    y_center = y1 + (y2 - y1) / 2
    return x_center, y_center


def fig_to_pil(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)

    pil_img = Image.open(buf)
    pil_img.show()


def plot_bbox_img(image, data):
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(image)

    if 'bboxes' in data and 'labels' in data:
        bboxes, labels = data['bboxes'], data['labels']
    elif 'bboxes' in data and 'bboxes_labels' in data:
        bboxes, labels = data['bboxes'], data['bboxes_labels']
    else:
        return fig_to_pil(fig)

    for bbox, label in zip(bboxes, labels):
        x1, y1, x2, y2 = bbox
        rect = patches.Rectangle((x1, y1), x2 - x1, y2 - y1, linewidth=2, edgecolor='indigo', facecolor='none')
        ax.add_patch(rect)
        x, y = get_center_coord(bbox)
        plt.scatter(x, y)
        plt.text(x1, y1, label, color='white', fontsize=10, bbox=dict(facecolor='indigo', alpha=0.8))

    ax.axis('off')
    return fig_to_pil(fig)


if __name__ == "__main__":
    while True:
        img_path = 'captured_image.png'
        objects = input('<USER>: ')
        res = get_objects_coord(img_path=img_path, objects=objects)
        print("<FL-2>: ", res)
        plot_bbox_img(Image.open(img_path), res['result'])
