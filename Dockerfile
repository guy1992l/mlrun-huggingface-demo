FROM mlrun/ml-models
RUN pip install transformers~=4.26.0 onnx~=1.10.1 onnxruntime~=1.11.1 optimum~=1.6.4 datasets~=2.10.1 onnxoptimizer 0.3.8