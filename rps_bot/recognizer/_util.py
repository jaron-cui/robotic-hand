def bbox_screen_to_cam(screen_bbox, frame_size):
    xmin, ymin, xsize, ysize = screen_bbox
    xmin = int(xmin * frame_size[1])
    ymin = int(ymin * frame_size[0])
    xsize = int(xsize * frame_size[1])
    ysize = int(ysize * frame_size[0])
    return xmin, ymin, xsize, ysize

def bbox_cam_to_screen(cam_bbox, frame_size):
    xmin, ymin, xsize, ysize = cam_bbox
    xmin /= frame_size[1]
    ymin /= frame_size[0]
    xsize /= frame_size[1]
    ysize /= frame_size[0]
    return xmin, ymin, xsize, ysize