from nixui.utils import cache


@cache.cache()
def fake_fn(intarg):
    return 5 + intarg


def test_cache_path_called_with_call_sig(mocker):
    mocker.patch('nixui.utils.cache._use_diskcache', return_value=True)
    mocker.patch('nixui.utils.cache._get_cache_path', side_effect=cache._get_cache_path)
    fake_fn(10)
    expected_call = mocker.call(
        ('nixui.tests.test_cache', 'fake_fn', (10,), ()),
        'hash_result'
    )
    assert expected_call in cache._get_cache_path.mock_calls


def test_unique_cache_for_version(mocker):
    call_args = ('foo', 'foo', 'foo', 'foo'), 'foo'

    mocker.patch('nixui.utils.cache._get_version', return_value='9.9.9')

    cache._get_cache_path.cache_clear()  # clear lru_cache
    path_0 = cache._get_cache_path(*call_args)

    cache._get_cache_path.cache_clear()  # clear lru_cache
    path_1 = cache._get_cache_path(*call_args)

    mocker.patch('nixui.utils.cache._get_version', return_value='5.5.5')

    cache._get_cache_path.cache_clear()  # clear lru_cache
    path_2 = cache._get_cache_path(*call_args)

    assert path_0 == path_1
    assert path_0 != path_2
