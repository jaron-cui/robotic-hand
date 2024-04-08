def bbox_screen_to_cam(screen_bbox, frame_shape):
    xmin, ymin, xsize, ysize = screen_bbox
    xmin = int(xmin * frame_shape[1])
    ymin = int(ymin * frame_shape[0])
    xsize = int(xsize * frame_shape[1])
    ysize = int(ysize * frame_shape[0])
    return xmin, ymin, xsize, ysize


def bbox_cam_to_screen(cam_bbox, frame_shape):
    xmin, ymin, xsize, ysize = cam_bbox
    xmin /= frame_shape[1]
    ymin /= frame_shape[0]
    xsize /= frame_shape[1]
    ysize /= frame_shape[0]
    return xmin, ymin, xsize, ysize
