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


def make_screen_roi_from_landmarks(landmarks: list, padding: float) -> list[float]:
    xmin = min([landmark.x for landmark in landmarks]) - padding
    xmax = max([landmark.x for landmark in landmarks]) + padding
    ymin = min([landmark.y for landmark in landmarks]) - padding
    ymax = max([landmark.y for landmark in landmarks]) + padding
    return [xmin, ymin, xmax - xmin, ymax - ymin]
