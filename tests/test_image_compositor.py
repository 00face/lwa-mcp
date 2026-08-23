import base64

from lwa_mcp.image_compositor import (
    ImageCompositor,
    ImageFrame,
    SixelDecoder,
    kitty_delete_sequence,
    kitty_graphics_sequence,
)


def test_kitty_png_payload_becomes_bounded_image_frame():
    payload = base64.b64encode(b"png-bytes").decode()
    frames, issue = ImageCompositor().extract_kitty(f"\x1b_Gf=100;{payload}\x1b\\")

    assert issue is None
    assert frames[0].mime_type == "image/png"
    assert frames[0].byte_length == len(b"png-bytes")


def test_kitty_payload_limit_is_enforced():
    payload = base64.b64encode(b"too-large").decode()
    frames, issue = ImageCompositor(max_bytes=2).extract_kitty(f"\x1b_Gf=100;{payload}\x1b\\")

    assert frames == []
    assert issue == "image payload exceeds compositor limit"


def test_malformed_kitty_payload_is_safe():
    frames, issue = ImageCompositor().extract_kitty("\x1b_Gf=100;not-base64!\x1b\\")

    assert frames == []
    assert issue == "malformed Kitty image payload"


def test_kitty_multipart_chunks_are_assembled_across_reads():
    compositor = ImageCompositor()
    first = base64.b64encode(b"png-").decode()
    second = base64.b64encode(b"bytes").decode()
    frames, issue = compositor.feed(f"\x1b_Ga=T,i=7,m=1;{first}\x1b\\")
    assert frames == []
    assert issue is None
    frames, issue = compositor.feed(f"\x1b_Ga=T,i=7,m=0;{second}\x1b\\")
    assert issue is None
    assert frames[0].data_base64 == base64.b64encode(b"png-bytes").decode()


def test_kitty_interleaved_image_ids_do_not_mix():
    compositor = ImageCompositor()
    part = lambda image_id, more, value: f"\x1b_Gi={image_id},m={more};{base64.b64encode(value).decode()}\x1b\\"
    assert compositor.feed(part("a", 1, b"a"))[0] == []
    assert compositor.feed(part("b", 1, b"b"))[0] == []
    a, _ = compositor.feed(part("a", 0, b"A"))
    b, _ = compositor.feed(part("b", 0, b"B"))
    assert base64.b64decode(a[0].data_base64) == b"aA"
    assert base64.b64decode(b[0].data_base64) == b"bB"


def test_sixel_decodes_a_single_solid_column_to_png():
    frame = SixelDecoder().decode('q#1;2;100;0;0~')
    assert frame.mime_type == "image/png"
    assert frame.width == 1
    assert frame.height == 6
    assert base64.b64decode(frame.data_base64).startswith(b"\x89PNG")


def test_sixel_limits_are_enforced():
    decoder = SixelDecoder(max_width=2)
    try:
        decoder.decode("q!3~")
    except ValueError as exc:
        assert "width" in str(exc)
    else:
        raise AssertionError("oversized Sixel did not fail closed")


def test_kitty_graphics_sequence_is_native_only_protocol_output():
    frame = ImageFrame("image/png", base64.b64encode(b"png").decode(), 3)
    sequence = kitty_graphics_sequence(frame, columns=4, rows=2)
    assert sequence.startswith("\x1b_Ga=T,f=100,q=2,c=4,r=2;")
    assert sequence.endswith("\x1b\\")
    assert "i=7" in kitty_graphics_sequence(frame, columns=4, rows=2, image_id=7)
    assert kitty_delete_sequence(7) == "\x1b_Ga=d,d=I,q=2,i=7;\x1b\\"


def test_kitty_raw_rgb_payload_is_composited_to_png():
    raw = bytes((255, 0, 0))
    payload = base64.b64encode(raw).decode()
    frames, issue = ImageCompositor().feed(f"\x1b_Gf=24,s=1,v=1;{payload}\x1b\\")
    assert issue is None
    assert frames[0].mime_type == "image/png"
    assert frames[0].width == 1
    assert frames[0].height == 1
