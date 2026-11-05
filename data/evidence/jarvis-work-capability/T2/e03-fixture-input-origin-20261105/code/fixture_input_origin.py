"""Metadata-only observation of messages in the owned fixture's WndProc.

This module neither injects input nor identifies a sender process. Native source
1 includes UIAccess injection. No key values, message payloads or text are kept.
"""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import datetime as dt
import itertools
import hashlib
import json
from pathlib import Path
import threading
import time


ORIGINS = {0: 'unavailable', 1: 'hardware_or_uiaccess',
           2: 'injected_non_uiaccess', 4: 'system'}
EXTRA_MESSAGES = {0x0051, 0x0281, 0x0282, 0x0283, 0x0285, 0x0288}


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def validate_origin_records(records, *, pid, controls, require_closed=True):
    _require(type(pid) is int and pid > 0 and len(controls) == 2
             and all(type(x) is int and x > 0 for x in controls)
             and len(set(controls)) == 2, 'origin fixture identity invalid')
    _require(isinstance(records, list) and 3 <= len(records) <= 10000,
             'origin record count invalid')
    start = {'schema': 1, 'type': 'origin-start', 'pid': pid, 'controls': controls}
    _require(records[0] == start, 'origin start/owned controls mismatch')
    stopped = records[-1].get('type') == 'origin-stop'
    _require(stopped or not require_closed, 'origin stop missing')
    messages = records[1:-1] if stopped else records[1:]
    keys = {'schema', 'type', 'entry_id', 'message_id', 'hwnd', 'pid', 'tid',
            'entered_ns', 'entered_at_utc', 'exited_ns', 'exited_at_utc', 'source',
            'send_flags_at_entry', 'parent_entry_id', 'parent_message_id',
            'ancestors', 'ancestors_truncated', 'depth', 'dispatch_returned'}
    by_id, probes = {}, set()
    control_counts = {str(control): {} for control in controls}
    for row in messages:
        _require(isinstance(row, dict) and set(row) == keys, 'origin record keys invalid')
        _require(row['schema'] == 1 and row['type'] == 'input-origin'
                 and row['pid'] == pid and row['hwnd'] in controls, 'origin record target mismatch')
        for name in ('entry_id', 'tid'):
            _require(type(row[name]) is int and row[name] > 0, 'origin ID invalid')
        for name in ('entered_ns', 'exited_ns', 'send_flags_at_entry', 'message_id', 'depth'):
            _require(type(row[name]) is int and row[name] >= 0, 'origin metadata unavailable')
        _require(row['entered_ns'] <= row['exited_ns'] and row['entry_id'] not in by_id,
                 'origin interval/entry ID invalid')
        _require(row['dispatch_returned'] is True and row['ancestors_truncated'] is False,
                 'origin dispatch/ancestry incomplete')
        for name in ('entered_at_utc', 'exited_at_utc'):
            _require(isinstance(row[name], str) and len(row[name]) <= 40
                     and dt.datetime.fromisoformat(row[name]).tzinfo is not None, 'origin timestamp invalid')
        source = row['source']
        _require(isinstance(source, dict) and set(source) == {'status', 'device_type', 'origin_id', 'origin'}
                 and source['status'] == 'available', 'origin source observation failed')
        _require(all(type(source[k]) is int and source[k] >= 0 for k in ('device_type', 'origin_id'))
                 and source['origin'] == ORIGINS.get(source['origin_id'], 'unrecognized'),
                 'origin source label/enum mismatch')
        ancestors = row['ancestors']
        _require(isinstance(ancestors, list) and len(ancestors) == row['depth'] <= 64,
                 'origin ancestor depth mismatch')
        previous = 0
        for ancestor in ancestors:
            _require(isinstance(ancestor, dict) and set(ancestor) == {'entry_id', 'message_id', 'hwnd'}
                     and type(ancestor['entry_id']) is int and previous < ancestor['entry_id'] < row['entry_id']
                     and type(ancestor['message_id']) is int and ancestor['message_id'] >= 0
                     and ancestor['hwnd'] in controls, 'origin ancestor invalid')
            previous = ancestor['entry_id']
        _require(row['parent_entry_id'] == (ancestors[-1]['entry_id'] if ancestors else None)
                 and row['parent_message_id'] == (ancestors[-1]['message_id'] if ancestors else None),
                 'origin parent mismatch')
        by_id[row['entry_id']] = row
        counts = control_counts[str(row['hwnd'])]
        key = str(row['message_id'])
        counts[key] = counts.get(key, 0) + 1
        if row['message_id'] == 0:
            probes.add(row['hwnd'])
    _require(probes == set(controls), 'origin owned-control probes missing')
    for row in messages:
        for ancestor in row['ancestors']:
            parent = by_id.get(ancestor['entry_id'])
            if parent is not None:
                _require(all(parent[key] == ancestor[key] for key in ('hwnd', 'message_id'))
                         and parent['tid'] == row['tid']
                         and parent['entered_ns'] <= row['entered_ns'] <= row['exited_ns'] <= parent['exited_ns'],
                         'origin nested interval/identity mismatch')
    if stopped:
        _require(records[-1] == dict(schema=1, type='origin-stop', pid=pid, complete=True,
                                     observed_records=len(messages), emitted_records=len(messages),
                                     errors=0, open_frames=0), 'origin stop/integrity mismatch')
    return {'status': 'PASS', 'closed': stopped, 'message_records': len(messages),
            'controls': controls, 'control_message_counts': control_counts,
            'sender_process_identified': False}


def validate_origin_audit(path, fixture, *, require_closed=True):
    raw = Path(path).read_bytes()
    _require(0 < len(raw) <= 4 * 1024 * 1024 and raw.endswith(b'\n'), 'origin file size/framing invalid')
    def unique(pairs):
        value = {}
        for key, item in pairs:
            _require(key not in value, 'origin duplicate JSON key')
            value[key] = item
        return value
    records = [json.loads(line.decode('utf-8'), object_pairs_hook=unique) for line in raw.splitlines()]
    result = validate_origin_records(records, pid=fixture['pid'],
                                     controls=[item['control_hwnd'] for item in fixture['targets']],
                                     require_closed=require_closed)
    return dict(result, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


class INPUT_MESSAGE_SOURCE(C.Structure):
    _fields_ = [('deviceType', C.c_int), ('originId', C.c_int)]


def bind_input_source_reader(user32, *, last_error=None):
    api = user32.GetCurrentInputMessageSource
    api.argtypes = [C.POINTER(INPUT_MESSAGE_SOURCE)]
    api.restype = W.BOOL
    last_error = last_error or C.get_last_error

    def read():
        value = INPUT_MESSAGE_SOURCE()
        if not api(C.byref(value)):
            return {'ok': False, 'error_code': int(last_error())}
        return {'ok': True, 'device_type': int(value.deviceType),
                'origin_id': int(value.originId)}
    return read


class InputOriginRecorder:
    """Wrap a fixture callback without changing its arguments or return value.

    A separate stack per receiving thread records unlogged parent messages too.
    Sidecar file order is completion order; entry IDs/intervals preserve nesting.
    Observation failures set complete=false and never suppress original dispatch.
    """

    def __init__(self, *, read_source, read_send_flags, emit, pid, thread_id,
                 clock_ns=time.perf_counter_ns, clock_utc=None):
        self.read_source, self.read_send_flags, self.emit = read_source, read_send_flags, emit
        self.pid, self.thread_id = pid, thread_id
        self.clock_ns = clock_ns
        self.clock_utc = clock_utc or (lambda: dt.datetime.now(dt.timezone.utc).isoformat())
        self._local = threading.local()
        self._ids = itertools.count(1)
        self._open_frames = 0
        self.observed_records = 0
        self.emitted_records = 0
        self.errors = 0
        self._started = False

    def start(self, controls):
        try:
            if self._started or len(controls) != 2 or any(type(x) is not int or x <= 0 for x in controls):
                raise ValueError('two owned control handles required once')
            self.emit({'schema': 1, 'type': 'origin-start', 'pid': self.pid,
                       'controls': list(controls)})
            self._started = True
            return True
        except Exception:
            self.errors += 1
            return False

    def finish(self):
        # A sidecar write failure must not skip the adapter's window cleanup.
        try:
            self.emit(dict(schema=1, type='origin-stop', pid=self.pid, **self.summary()))
        except Exception:
            self.errors += 1
        return self.summary()

    def _source(self):
        try:
            result = self.read_source()
            if result.get('ok') is not True:
                self.errors += 1
                code = result.get('error_code')
                return {'status': 'unavailable', 'error_code': code if type(code) is int else None}
            device, origin = result['device_type'], result['origin_id']
            if type(device) is not int or type(origin) is not int or min(device, origin) < 0:
                raise ValueError('invalid input source enums')
            return {'status': 'available', 'device_type': device, 'origin_id': origin,
                    'origin': ORIGINS.get(origin, 'unrecognized')}
        except Exception as exc:
            self.errors += 1
            return {'status': 'error', 'error_type': type(exc).__name__}

    def summary(self):
        return {'complete': self._started and self.errors == 0 and self._open_frames == 0
                and self.observed_records == self.emitted_records,
                'observed_records': self.observed_records,
                'emitted_records': self.emitted_records,
                'errors': self.errors, 'open_frames': self._open_frames}

    def wrap(self, original, *, enabled, observed):
        def dispatch(hwnd, message, wparam, lparam):
            if not enabled():
                return original(hwnd, message, wparam, lparam)
            stack = getattr(self._local, 'stack', None)
            if stack is None:
                stack = self._local.stack = []
            frame = {'entry_id': next(self._ids), 'message_id': int(message),
                     'hwnd': int(hwnd)}
            record = None
            if observed(message):
                self.observed_records += 1
                try:
                    entered_ns, entered_utc = self.clock_ns(), self.clock_utc()
                    # Capture before any text readback or original WndProc call.
                    source = self._source()
                    try:
                        flags = self.read_send_flags()
                        if type(flags) is not int or flags < 0:
                            raise ValueError('invalid send flags')
                    except Exception:
                        flags = None
                        self.errors += 1
                    record = dict(frame, schema=1, type='input-origin', pid=self.pid,
                                  tid=self.thread_id(), entered_ns=entered_ns,
                                  entered_at_utc=entered_utc, source=source,
                                  send_flags_at_entry=flags,
                                  parent_entry_id=stack[-1]['entry_id'] if stack else None,
                                  parent_message_id=stack[-1]['message_id'] if stack else None,
                                  ancestors=[dict(item) for item in stack[-64:]],
                                  ancestors_truncated=len(stack) > 64, depth=len(stack))
                    if len(stack) > 64:
                        self.errors += 1
                except Exception:
                    self.errors += 1
                    return original(hwnd, message, wparam, lparam)
            stack.append(frame)
            self._open_frames += 1
            returned = False
            try:
                result = original(hwnd, message, wparam, lparam)
                returned = True
                return result
            finally:
                stack.pop()
                self._open_frames -= 1
                if record is not None:
                    try:
                        record.update(exited_ns=self.clock_ns(), exited_at_utc=self.clock_utc(),
                                      dispatch_returned=returned)
                        self.emit(record)
                        self.emitted_records += 1
                    except Exception:
                        self.errors += 1
        return dispatch
