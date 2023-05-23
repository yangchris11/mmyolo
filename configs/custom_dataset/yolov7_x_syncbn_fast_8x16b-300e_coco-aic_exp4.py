_base_ = '../yolov7/yolov7_l_syncbn_fast_8x16b-300e_coco.py'

max_epochs = 20
data_root = '/media/sda1/AI_city_2023/'

# 结果保存的路径，可以省略，省略保存的文件名位于 work_dirs 下 config 同名的文件夹中
# 如果某个 config 只是修改了部分参数，修改这个变量就可以将新的训练文件保存到其他地方
# work_dir = './work_dirs/yolov5_s-v61_syncbn_fast_1xb32-100e_cat'

# load_from 可以指定本地路径或者 URL，设置了 URL 会自动进行下载，因为上面已经下载过，我们这里设置本地路径
# 因为本教程是在 cat 数据集上微调，故这里需要使用 `load_from` 来加载 MMYOLO 中的预训练模型，这样可以在加快收敛速度的同时保证精度
#load_from = './work_dirs/yolov5_s-v61_syncbn_fast_8xb16-300e_coco_20220918_084700-86e02187.pth'  # noqa
load_from = "/home/cycyang/mmyolo/checkpoints/exp3_epoch_100.pth"
#load_from = 'https://download.openmmlab.com/mmyolo/v0/yolov7/yolov7_x_syncbn_fast_8x16b-300e_coco/yolov7_x_syncbn_fast_8x16b-300e_coco_20221124_215331-ef949a68.pth'

# 根据自己的 GPU 情况，修改 batch size，YOLOv5-s 默认为 8卡 x 16bs
train_batch_size_per_gpu = 12
train_num_workers = 8  # 推荐使用 train_num_workers = nGPU x 4

save_epoch_intervals = 5  # 每 interval 轮迭代进行一次保存一次权重

# 根据自己的 GPU 情况，修改 base_lr，修改的比例是 base_lr_default * (your_bs / default_bs)
base_lr = 0.00025

# anchors = [  # 此处已经根据数据集特点更新了 anchor，关于 anchor 的生成，后面小节会讲解
#     [(68, 69), (154, 91), (143, 162)],  # P3/8
#     [(242, 160), (189, 287), (391, 207)],  # P4/16
#     [(353, 337), (539, 341), (443, 432)]  # P5/32
# ]

class_name = ('person', )  # 根据 class_with_id.txt 类别信息，设置 class_name
num_classes = len(class_name)
metainfo = dict(
    classes=class_name,
    palette=[(220, 20, 60)]  # 画图时候的颜色，随便设置即可
)

train_cfg = dict(
    max_epochs=max_epochs,
    val_begin=0,  # 第几个 epoch 后验证，这里设置 20 是因为前 20 个 epoch 精度不高，测试意义不大，故跳过
    val_interval=save_epoch_intervals  # 每 val_interval 轮迭代进行一次测试评估
)

model = dict(
    backbone=dict(arch='X'),
    neck=dict(
        in_channels=[640, 1280, 1280],
        out_channels=[160, 320, 640],
        block_cfg=dict(
            type='ELANBlock',
            middle_ratio=0.4,
            block_ratio=0.4,
            num_blocks=3,
            num_convs_in_block=2),
        use_repconv_outs=False),
    bbox_head=dict(head_module=dict(in_channels=[320, 640, 1280])))

train_dataloader = dict(
    batch_size=train_batch_size_per_gpu,
    num_workers=train_num_workers,
    dataset=dict(
        _delete_=True,
        type='RepeatDataset',
        # 数据量太少的话，可以使用 RepeatDataset ，在每个 epoch 内重复当前数据集 n 次，这里设置 5 是重复 5 次
        times=1,
        dataset=dict(
            type=_base_.dataset_type,
            data_root=data_root,
            metainfo=metainfo,
            ann_file='annotations/train_all_val_all_sr_20_10_img_77154.json',
            data_prefix=dict(img=''),
            filter_cfg=dict(filter_empty_gt=False, min_size=32),
            pipeline=_base_.train_pipeline)))

val_dataloader = dict(
    dataset=dict(
        metainfo=metainfo,
        data_root=data_root,
        ann_file='annotations/train_all_val_all_sr_600_0_img_2569.json',
        data_prefix=dict(img='')))

test_dataloader = val_dataloader

val_evaluator = dict(ann_file=data_root + 'annotations/train_all_val_all_sr_600_0_img_2569.json')
test_evaluator = val_evaluator

optim_wrapper = dict(optimizer=dict(lr=base_lr))

default_hooks = dict(
    # 设置间隔多少个 epoch 保存模型，以及保存模型最多几个，`save_best` 是另外保存最佳模型（推荐）
    checkpoint=dict(
        type='CheckpointHook',
        interval=save_epoch_intervals,
        max_keep_ckpts=10,
        save_best='auto'),
    param_scheduler=dict(max_epochs=max_epochs),
    # logger 输出的间隔
    logger=dict(type='LoggerHook', interval=10))

visualizer = dict(vis_backends=[dict(type='LocalVisBackend'),dict(type='TensorboardVisBackend')])