Projects that deal with hardware noise itself, rather than with the algorithm being run. They
typically do one or more of:

 * **detection**: instrumenting a computation so that a faulty run can be recognized, such as
   Pauli checks, flag qubits, syndrome extraction, or post-selection on an ancilla outcome,
 * **correction**: encoding logical information redundantly and acting on what the detection
   reveals, such as error-correcting or error-detecting codes, decoders, and the circuits and
   tooling needed to build or evaluate them,
 * **mitigation**: leaving the errors in place but removing their bias from the final estimate,
   such as readout error mitigation, zero-noise extrapolation, or probabilistic error
   cancellation,
 * **characterization**: learning the noise itself (for example the noise model of a layer), as
   an input to one of the above.

A technique that suppresses errors while a circuit is being compiled belongs in
[transpiler plugin](#transpiler-plugin) instead: if it can be expressed as a transpiler pass,
implementing the plugin interface makes it usable from any Qiskit workflow for free.

More information:
[Error suppression and mitigation techniques](https://quantum.cloud.ibm.com/docs/en/guides/error-mitigation-and-suppression-techniques)
