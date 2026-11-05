import fixture_adapter as f


def test_message_kind_classifies_input_and_programmatic_edits():
    assert f.message_kind(0x0000)==('WM_NULL','probe')
    assert f.message_kind(0x0102)==('WM_CHAR','input')
    assert f.message_kind(0x010F)==('WM_IME_COMPOSITION','input')
    assert f.message_kind(0x000C)==('WM_SETTEXT','programmatic')
    assert f.message_kind(0x00C2)==('EM_REPLACESEL','programmatic')
    assert f.message_kind(0x1234) is None


def test_audit_record_redacts_raw_text_and_message_payload():
    record=f.make_audit_record(
        message=0x0102,hwnd=10,pid=20,tid=30,received_at_utc='2026-11-04T00:00:00Z',
        qpc_ns=123456,last_input_tick_before=76,last_input_tick_after=77,
        foreground_before_hwnd=9,focus_before_hwnd=8,foreground_after_hwnd=10,focus_after_hwnd=11,
        in_send_message=False,
        before_text='PRIVATE BEFORE',after_text='PRIVATE AFTER')
    assert record['message']=='WM_CHAR'
    assert record['category']=='input'
    assert record['before']=={'utf16_units':14,'sha256_utf16le':f.text_digest('PRIVATE BEFORE')}
    assert record['after']=={'utf16_units':13,'sha256_utf16le':f.text_digest('PRIVATE AFTER')}
    assert record['last_input_tick_before']==76 and record['last_input_tick_after']==77
    assert record['foreground_before_hwnd']==9 and record['focus_before_hwnd']==8
    assert record['foreground_after_hwnd']==10 and record['focus_after_hwnd']==11
    assert 'wparam' not in record and 'lparam' not in record and 'text' not in record
    assert 'PRIVATE' not in repr(record)


def test_non_mutating_messages_are_not_audit_records():
    assert f.make_audit_record(message=0x000D) is None
