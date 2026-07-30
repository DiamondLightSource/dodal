from dodal.devices.selectable_source import SelectedSource, get_obj_from_selected_source


def test_get_obj_from_selected_source() -> None:
    obj1, obj2 = 1, 2
    selected_obj = get_obj_from_selected_source(SelectedSource.SOURCE1, obj1, obj2)
    assert selected_obj is obj1
    selected_obj = get_obj_from_selected_source(SelectedSource.SOURCE2, obj1, obj2)
    assert selected_obj is obj2
