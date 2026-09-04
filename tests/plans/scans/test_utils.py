# import re

# import pytest

# from dodal.devices.motors import Motor
# from dodal.plans.scans.annotations import Number
# from dodal.plans.scans.utils import (
#     _make_stepped_list_num,
#     _make_stepped_list_step,
#     _round_list_elements,
#     make_step_grid_scan_args_and_shape,
#     make_step_scan_args_and_shape,
# )


# @pytest.mark.parametrize(
#     "x_list, y_list, grid, final_shape, final_length",
#     (
#         [[0, 10, 1], [0, 5], False, (11,), 4],
#         [[0, 10, 1], [0, 5, 1], True, (11, 6), 4],
#     ),
# )
# def test_make_step_scan_args_and_shape(
#     x_axis: Motor,
#     x_list: list,
#     y_axis: Motor,
#     y_list: list,
#     grid: bool,
#     final_shape: list,
#     final_length: int,
# ):
#     args, shape = make_step_scan_args_and_shape(
#         params=[x_axis, *x_list, y_axis, *y_list], grid=grid
#     )
#     assert len(args) == final_length
#     assert shape == final_shape


# def test_make_list_scan_args_fails_when_lists_are_different_lengths(
#     x_axis: Motor,
#     y_axis: Motor,
# ):
#     with pytest.raises(ValueError):
#         _make_step_scan_args_and_shape(
#             params=[x_axis, 0, 1, 2, y_axis, 0, 1, 2, 3], grid=False
#         )


# @pytest.mark.parametrize(
#     "stepped_list, params, rounded_element",
#     (
#         [[0.1234, 1.1234, 2.1234], [0.123, 2.123, 1], 0.123],
#         [[0.1234, 1.1234, 2.1234], [0.12, 2.12, 1], 0.12],
#         [[0.1234, 1.1234, 2.1234], [0.1, 2.1, 1], 0.1],
#         [[0.1234, 1.1234, 2.1234], [0, 2, 1], 0],
#     ),
# )
# def test_round_list_elements(
#     stepped_list: list[float], params: list[float], rounded_element: float
# ):
#     rounded_list = _round_list_elements(stepped_list, params)
#     assert rounded_list[0] == rounded_element


# @pytest.mark.parametrize(
#     "start, stop, step",
#     (
#         [-1, 1, 0.1],
#         [-2, 2, 0.2],
#         [1, -1, -0.1],
#         [2, -2, -0.2],
#         [1, -1, 0.1],
#         [2, -2, 0.2],
#     ),
# )
# def test_make_stepped_list_step(start: float, stop: float, step: float):
#     stepped_list = _make_stepped_list_step(start, stop, step)
#     stepped_list_length = len(stepped_list)
#     assert stepped_list_length == 21
#     assert stepped_list[0] / stepped_list[-1] == -1
#     assert stepped_list[10] == 0


# def test_make_stepped_list_step_with_large_step():
#     stepped_list = _make_stepped_list_step(0, 1, 5)
#     stepped_list_length = len(stepped_list)
#     assert stepped_list_length == 2
#     assert stepped_list[0] == 0
#     assert stepped_list[-1] == 1


# @pytest.mark.parametrize("start, step", ([-1, 0.1], [-2, 0.2], [1, -0.1], [2, -0.2]))
# def test_make_stepped_list_num(start: float, step: float):
#     stepped_list = _make_stepped_list_num(start, step, num=21)
#     stepped_list_length = len(stepped_list)
#     assert stepped_list_length == 21
#     assert stepped_list[0] / stepped_list[-1] == -1
#     assert stepped_list[10] == 0


# def test_make_stepped_list_num_fails_when_num_is_zero():
#     start = stop = 1.1
#     with pytest.raises(
#         ValueError,
#         match=re.escape(
#             f"Start ({start}) and stop ({stop}) values cannot be the same."
#         ),
#     ):
#         _make_stepped_list_step(start=start, stop=stop, step=0.25)


# def test_make_stepped_list_num_fails_when_given_equal_start_and_stop_values():
#     with pytest.raises(
#         ValueError,
#         match=re.escape("Number of points (0) and number of steps (0) cannot be zero."),
#     ):
#         _make_stepped_list_num(start=1, step=0, num=0)


# @pytest.mark.parametrize(
#     "x_list, y_list, z_list, grid",
#     (
#         [[0, 1], [0, 0.2], [0, 0.5], False],
#         [[0, 1, 0.25], [0, 0.2], [0, 1, 0.2, 0.5], False],
#         [[0, 1, 0.25], [0, 0.2], [0, 1, 0.5], True],
#         [[0, 1, 0.25], [0, 1, 0.2], [0, 0.5], True],
#     ),
# )
# def test_make_step_scan_args_fails_when_given_incorrect_number_of_parameters(
#     x_axis: Motor,
#     x_list: list[Number],
#     y_axis: Motor,
#     y_list: list[Number],
#     z_axis: Motor,
#     z_list: list[Number],
#     grid: bool,
# ):
#     with pytest.raises(ValueError):
#         make_step_scan_args_and_shape(
#             params=[x_axis, *x_list, y_axis, *y_list, z_axis, *z_list], grid=grid
#         )


# def test_make_step_scan_args_and_shape_fails_with_invalid_type_args(
#     x_axis: Motor,
#     y_axis: Motor,
# ):
#     with pytest.raises(
#         ValueError,
#         match="Scan syntax only takes movables or numbers as parameters.",
#     ):
#         make_step_scan_args_and_shape(
#             [x_axis, 1, "3", 1, y_axis, 1, "4", 1],  # type: ignore
#             grid=True,
#         )
#         make_step_scan_args_and_shape(
#             [x_axis, 1, "3", 1, y_axis, 1, "4"],  # type: ignore
#             grid=False,
#         )
