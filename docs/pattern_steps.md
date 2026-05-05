[Qiskit Patterns](https://quantum.cloud.ibm.com/docs/en/guides/intro-to-patterns) are a structured four-step development workflow suggested by IBM Quantum to structure modules on quantum application.

## Map the problem

Translate domain-specific problems into quantum circuits and operators.

## Optimize for hardware

Transpile and optimize circuits into ISA (Instruction Set Architecture) circuits (mapping to physical qubits, converting to hardware basis gates, and reducing operations) to maximize success on the target device.

## Execute on hardware

Run ISA circuits on hardware using quantum primitives (such as Sampler or Estimator primitives).

## Post-process results

Process quantum outputs (bitstrings from Sampler, or expectation values from Estimator) using classical techniques (such as readout error mitigation, post-selection on physical properties, and marginalization) to extract meaningful, domain-relevant results.