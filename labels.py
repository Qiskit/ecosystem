import json
import os

members_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ecosystem', 'resources',
                            'members.json')
print(members_path)
with open(members_path, "r") as f:
    data = json.load(f)

print(sorted(set().union(*[j['labels'] for i in data.values() for j in i.values()])))
"""
['QAMP', 'QEC', 'algorithms', 'chemistry', 'circuit', 'circuit simulator', 'converter',
'differential-equations', 'error mitigation', 'finance', 'game', 'hardware', 'julia', 'library', 'machine learning', 'optimization', 'paper implementation', 'partner', 'physics', 'plugin', 'prototype', 'provider', 'qasm', 'simulation', 'tool']

['QAMP', 'QEC', 'algorithms', 'chemistry', 'circuit', 'circuit simulator', 'converter', 'error mitigation', 'finance', 'game', 'hardware', 'julia', 'library', 'machine learning', 'openqasm', 'optimization', 'paper implementation', 'partner', 'physics', 'plugin', 'prototype', 'provider', 'simulation', 'tool']

Removes from the template labels without a clear definition
 - fork
 - sdk
 - demo
 - tool
 - runtime
 - library
 - hardware
Adjust labels for members:
  - qiskit-ibm-runtime is a provider
  - bosonic-qiskit is for quantum simulation
  - pytorch-quantum relabeled as `machine learning`
  - mitiq relabeled as `error mitigation` 
  - pennylane-qiskit relabeled as `converter`
  - `algorithm` unified with `algorithms`
  - Aer as `circuit simulator` to distinguish from quantum `simulation`
Some branding issues:
  - qiskit-qec and other qiskit-* applications is not part of Qiskit itself.
  - bosonic-qiskit use wrong Qiskit capitalization
  - `qasm` renamed as `openqasm`
  - `pulse` renamed as `openpulse`

"""
