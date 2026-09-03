Quantum hardware is noisy, and that noise biases the outcome of a computation.
Projects in this category reduce that bias on today's devices, without relying on
fault-tolerant hardware. They act around the execution of a circuit, rather than inside it:

 * by randomizing or instrumenting the circuit before it runs, such as Pauli twirling or
   adding checks whose outcome flags a faulty run,
 * by post-processing the results of many executions to estimate the noise-free value,
   such as readout error mitigation, zero-noise extrapolation, or probabilistic error cancellation.

The cost is usually paid in sampling overhead: several circuit executions are needed to produce
a single mitigated result.

A technique that suppresses errors while a circuit is being compiled belongs in
[transpiler plugin](#transpiler-plugin) instead: if it can be expressed as a transpiler pass,
implementing the plugin interface makes it usable from any Qiskit workflow for free.

More information:
[Error suppression and mitigation techniques](https://quantum.cloud.ibm.com/docs/en/guides/error-mitigation-and-suppression-techniques)
