# Fruit-Fly Connectome and Embodied-Brain Demos — Evidence Review

**Project:** KMH OIA / Operating Intelligence Architecture  
**Review date:** 2026-10-20  
**Status:** Research synthesis; not a reproduction or independent benchmark  
**Decision:** Do not treat a connectome map, a simulation demo, or a task score as evidence of a biological brain upload, general autonomy, or consciousness.

## Executive finding

Three claims must be evaluated separately:

1. **Connectome reconstruction:** an electron-microscopy-derived graph of neurons and synaptic connections.
2. **Computational simulation / embodiment:** a mathematical neural model is run and connected to a virtual body or task environment through explicit input and output mappings.
3. **Autonomous cognition:** the system forms goals, learns online, generalizes robustly, or demonstrates consciousness.

The first category has strong peer-reviewed evidence. The second has meaningful research prototypes, but usually with simplifying assumptions, engineered sensory encoders, trained readouts/controllers, reduced subgraphs, or optional external search. The third is **not established by the demos reviewed here**. This is an evidence boundary, not a proof that machine consciousness is impossible.

## Evidence labels

- **Primary research / dataset source:** peer-reviewed paper or dataset publisher.
- **Project-reported result:** author-maintained technical documentation or code; useful, but not an independent replication.
- **Secondary reporting:** useful for timeline and claim checking, not a substitute for methods.
- **Unverified claim:** critical methods or reproducible artifacts were not located in sources reviewed on 2026-10-20.

## 1. Connectome datasets: counts require scope and definition

| Dataset / source | Published scope and count | How to interpret |
|---|---|---|
| FlyWire adult female fly brain (Nature, 2024) | 139,255 neurons; 54.5 million synapses | Whole adult brain reconstruction. It is a wiring map, not by itself a running neural model. |
| Male CNS (Google Research / Janelia, 2026) | Public summary reports over 166,000 neurons and 125 million synaptic connections | Brain plus central nerve cord. Dataset release and derived graph reports can use different inclusion/counting definitions. |
| FlyWire–BANC female brain and nerve cord (Nature, 2026) | 155,916 proofread and roughly proofread neurons reported | Brain-and-nerve-cord scope; the paper notes that 9,390 lamina neurons are absent from this dataset. Do not invent a synapse total where the cited summary does not provide one. |
| ChessFly-derived model graph | 138,639 neurons; 15,091,983 connections | A model-specific subset/representation; do not compare these numbers directly with the whole FlyWire paper's synapse count without checking graph construction. |
| FlyCube-derived MaleCNS graph | README reports 166,700 retained neurons and 25,582,938 imported edges; an 8,192-neuron subgraph is used for training | The repository documents its import and subgraph choices. The lower edge count should be treated as a model/representation count, not silently substituted for the publisher's synapse count. |

**Important reconciliation rule:** “neuron,” “synapse,” “edge,” “retained neuron,” and “training subgraph neuron” may be counted at different stages. Keep the publisher's dataset count separate from counts after filtering, edge extraction, thresholding, graph conversion, or subgraph sampling. Before comparing counts, record dataset release/version, inclusion criteria, edge definition, and checksum.

Sources:
- FlyWire Nature paper: https://www.nature.com/articles/s41586-024-07558-y
- Google Research Male CNS overview: https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/
- BANC Nature paper: https://www.nature.com/articles/s41586-026-10735-w
- FlyWire data access overview: https://github.com/seung-lab/FlyConnectome

## 2. Embodied simulation: Eon Systems

Eon's technical post describes a loop that maps virtual-world sensory events into identified sensory neurons/pathways, updates a connectome-constrained neural model, converts selected descending-neuron outputs into low-dimensional motor commands, and feeds resulting body motion back as new sensory state. The post states a 15 ms brain/body synchronization interval and a NeuroMechFly body with 87 articulated joints in MuJoCo.

Key caveats disclosed by Eon:
- The neuron model uses leaky-integrate-and-fire (LIF) dynamics and simplified synapses; it does not reproduce detailed multicompartment dendrites or the full variety of biophysical channel dynamics.
- Walking uses existing or slightly modified controllers trained to imitate fly locomotion; selected descending outputs modulate those controllers.
- Some visual activations are described by Eon as not yet substantially influencing behavioral outputs.
- At the time of the post, some behaviors such as embodied escape were not yet implemented.

**Interpretation:** this is meaningful brain/body integration research, not evidence that a complete biological fly has been uploaded. For causal attribution, measure what the neural model contributes separately from the body simulator and trained controllers.

Source: https://eon.systems/updates/embodied-brain-emulation

## 3. Task demos: architecture matters

### ChessFly

The model card reports a FlyWire-derived graph of 138,639 neurons and 15,091,983 connections. Anatomy and excitatory/inhibitory signs are fixed, while the board encoder, connection gains, per-neuron/step gains and thresholds, and output decoder are trained on 4.4 million Stockfish-annotated Lichess positions. Its reported recovery of Stockfish's top move is 30.4%. The browser Space adds depth-3 search on top.

**Interpretation:** this is evidence that a fixed connectome-shaped graph can be adapted for chess-related prediction. It is not evidence of biological chess cognition: task input encoding, fitted parameters, supervised labels, decoder, and additional search all matter.

Sources:
- Model card: https://huggingface.co/mlabonne/chessfly
- Browser Space description: https://huggingface.co/spaces/mlabonne/chessfly

### FlyCube (Rubik's Cube)

The public repository reports a measured MaleCNS-derived connectome in a cube-solving loop, with a real cube-state environment, engineered sticker encoder, recurrent rate network, policy/value outputs, and two inference modes: policy-only and brain-plus-bounded-search. Training uses conventional cube-solving teachers offline (including Kociemba / exact-search-style labels); the README says the teacher is not available to the live inference path.

The repo is unusually explicit about limitations and incidents:
- It uses an 8,192-neuron training subgraph rather than simulating the full CNS model during training/inference.
- Reported benchmark tables label the first 60-minute checkpoints as **legacy reversed-connectivity** results; the repository says corrected propagation is now the default.
- Those legacy tables report zero solved cases out of 100 uniform random states, while short shallow suites fare better.
- These are project-reported results, not an independent scientific replication.

**Interpretation:** a promising reproducibility-oriented prototype and a useful example of separating a trained policy from external search. Before accepting the newer implementation's performance, inspect its checkpoint provenance and run the published tests/evaluation on the corrected propagation path.

Source: https://github.com/lntegrals/flycube-public

### Independent comparison prototype: FLY-lab

A recent public repository describes a controlled comparison using the same NeuroMechFly body and low-level controller across a connectome, simple hand-written rules, replayed brain output, and degree-preserving shuffled networks. Its README reports that simple rules and the connectome both solved the small left/right touch-response tasks, while replayed output failed; it also reports no connectome advantage over a two-line controller for those tasks.

**Interpretation:** this is an important counterexample to reading realistic motion as proof that the connectome caused the behavior. It remains a repository-reported, task-specific result; inspect the protocol, artifacts and independent reproducibility before generalizing.

Source: https://github.com/Recluse/FLY-lab

## 4. Odyssey-3 fly demo — unverified technical claim

On 17 October 2026, Odyssey publicly claimed that it placed a fruit-fly brain inside its Odyssey-3 world model and showed the fly moving through generated virtual environments. Sources reviewed through 20 October reported no accompanying paper, code repository, methods note, or technical documentation identifying the specific brain model or describing the sensory-input and motor-output interfaces.

What remains unknown:
- Which connectome and neural dynamics, if any, are used.
- Whether generated-world observations are fed into a neural model as sensory input.
- How the fly's computed neural outputs are translated into flight control.
- Whether a conventional or learned flight controller supplies most of the movement.
- Whether the demo is reproducible and which behaviors are measured.

**Status:** public demo claim; technical validation pending. A short video can show rendered motion, but cannot by itself identify the control path or prove autonomy.

Sources:
- Odyssey claim analysis (19 Oct 2026): https://traictory.com/news/2026-10-19-fly-brain-odyssey-3-world-model
- Independent demo/method check (18 Oct 2026): https://shaduf.ai/p/digital-fly-catalog/reports/2026-10-18-run19/

## 5. Autonomy and consciousness: what the evidence does and does not show

The sources reviewed support connectome reconstruction and several forms of simulated neural computation. They do **not** establish that the simulations:
- create their own goals or drives;
- learn from ongoing experience through biologically faithful plasticity;
- generalize reliably to novel environments without task-specific engineering;
- operate independently of learned motor controllers, trained encoders/readouts, or external search; or
- have subjective experience or consciousness.

Do not infer absence of consciousness solely from a missing feature, and do not infer consciousness from lifelike animation. Treat consciousness as **not demonstrated and not assessed by these task benchmarks**.

## 6. KMH OIA evidence-gate proposal

Use the following gates before accepting any “brain-driven” or “autonomous” claim. These are proposed checks, **not completed tests**.

- [ ] **EG-FLY-01 — Provenance:** pin the dataset release, sex/scope, data license, graph-construction code, model version and checksums.
- [ ] **EG-FLY-02 — Interface trace:** retain timestamped sensory inputs, neural states/outputs, controller commands and resulting body/environment states for each run.
- [ ] **EG-FLY-03 — Causal ablation:** run matched conditions with the live connectome, silenced network, degree-preserving shuffled graph, fixed output replay and simple baseline controller.
- [ ] **EG-FLY-04 — Learning claim:** distinguish offline supervised/RL training from online learning during the evaluated episode; document exactly which parameters can change.
- [ ] **EG-FLY-05 — Generalization:** predefine held-out environments/stimuli/seeds and report successes, failures, timeouts and latency.
- [ ] **EG-FLY-06 — Independent reproduction:** provide scripts, environment lockfiles, model/checkpoint hashes, raw result files and a one-command reproduction path.
- [ ] **EG-FLY-07 — Claim calibration:** use “connectome-based simulation,” “embodied neural model,” or “task demo” unless stronger claims pass predefined measurements.

**Release rule:** no next evidence gate passes on a video alone. Keep the claim status **UNVERIFIED** until the code/data path and evaluation results are available and checked.

## References and review limits

This note combines primary publications, author-maintained project documentation and recent secondary reporting. ChessFly, FlyCube and FLY-lab results above are identified as project-reported where applicable. Odyssey-3 remains unverified in the absence of public methods/code. This review did not execute any of the third-party demos or independently reproduce their scores.

- FlyWire Nature (2024): https://www.nature.com/articles/s41586-024-07558-y
- Google Research Male CNS (2026): https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/
- BANC Nature (2026): https://www.nature.com/articles/s41586-026-10735-w
- Eon Systems embodied fly: https://eon.systems/updates/embodied-brain-emulation
- ChessFly model: https://huggingface.co/mlabonne/chessfly
- FlyCube: https://github.com/lntegrals/flycube-public
- FLY-lab controlled comparison: https://github.com/Recluse/FLY-lab
- Odyssey-3 claim review: https://traictory.com/news/2026-10-19-fly-brain-odyssey-3-world-model
- Odyssey-3 methods check: https://shaduf.ai/p/digital-fly-catalog/reports/2026-10-18-run19/
