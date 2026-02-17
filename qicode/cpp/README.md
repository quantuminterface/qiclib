# QiCode C++ Bindings

C++ bindings for QiCode protocol buffers.

## Dependencies

- **Protobuf**: >= 5.27.2 (for protocol buffer support)
- **CMake**: >= 3.20

## Building from Source

```bash
conan create . --build=missing
```

To use the library in your own Conan project:

```
[requires]
qicode/0.0.1
```
