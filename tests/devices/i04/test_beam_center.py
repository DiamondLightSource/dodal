def test_binary_img():
    ...
    # Patch each cv2 function that is used. For each one, do assert_called_once_with(...). Also set return value for
    # cv2.threshold and assert binary_img() == this return value


def test_fit_ellipse_good_params():
    ...
    # patch cv2 functiosn and assert_called_once_with, assert return value is correct by setting return value of
    # the cv2.fitellipse magicmock


def test_fit_ellipse_raises_error_if_not_enough_image_points():
    with pytest.raises(ValueError, match="No contours found in image."):
        ...


def test_fit_ellipse_raises_error_if_not_enough_contour_points(): ...
