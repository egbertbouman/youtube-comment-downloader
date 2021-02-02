from downloader import search_dict


def test_that_nothing_is_yielded_from_empty_dict():
    assert not list(search_dict({}, "test"))


def test_that_correct_value_is_yielded_for_simple_dictionaries():
    assert list(search_dict({"test": "expected"}, "test")) == ["expected"]


def test_that_correct_value_is_yielded_when_dictionary_is_inside_list():
    assert list(search_dict([{"test": "expected"}], "test")) == ["expected"]


def test_that_two_values_are_yielded_if_key_is_found_twice_in_nested_dictionaries():
    assert (
        list(search_dict([{"test": "expected"}, {"test": "expected"}], "test"))
        == ["expected"] * 2
    )


def test_that_expected_value_is_yielded_when_nesting_dictionaries():
    assert (
        list(
            search_dict({"a": {"test": "expected"}, "b": {"test": "expected"}}, "test")
        )
        == ["expected"] * 2
    )


def test_benchmark_search(benchmark):
    test_dict = {index: list(range(10)) for index in range(1, 30)}
    benchmark(lambda: list(search_dict(test_dict, "test")))
