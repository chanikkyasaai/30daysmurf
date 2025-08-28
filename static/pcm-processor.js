// This AudioWorkletProcessor converts the incoming microphone audio
// from 32-bit float to 16-bit PCM, downsamples it to 16kHz,
// and sends it back to the main thread.

class PCMProcessor extends AudioWorkletProcessor {
  // Downsample from the source sample rate to 16kHz
  static downsampleBuffer(buffer, inputSampleRate, outputSampleRate) {
    if (inputSampleRate === outputSampleRate) {
      return buffer;
    }
    const sampleRateRatio = inputSampleRate / outputSampleRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    let offsetResult = 0;
    let offsetBuffer = 0;
    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
      let accum = 0;
      let count = 0;
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      result[offsetResult] = accum / count;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    return result;
  }

  // Convert a Float32Array to a 16-bit PCM Int16Array
  static floatTo16BitPCM(input) {
    const output = new Int16Array(input.length);
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]));
      output[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return output;
  }

  process(inputs, outputs, parameters) {
    // We expect only one input, with one channel
    const input = inputs[0];
    if (input.length > 0) {
      const inputData = input[0];
      
      // `sampleRate` is a global variable in the AudioWorklet scope.
      const downsampled = PCMProcessor.downsampleBuffer(inputData, sampleRate, 16000);
      
      const pcm16 = PCMProcessor.floatTo16BitPCM(downsampled);

      // Post the transferable buffer back to the main thread
      this.port.postMessage(pcm16.buffer, [pcm16.buffer]);
    }
    
    // Keep the processor alive
    return true;
  }
}

registerProcessor('pcm-processor', PCMProcessor);
