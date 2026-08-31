import paddle

print("Paddle version :", paddle.__version__)
print("Compiled with CUDA :", paddle.is_compiled_with_cuda())
print("Device :", paddle.get_device())