<!-- PROJECT LOGO -->
<br />
<p align="center">
<a href="#"><img src="docs/source/_static/Banner.svg" alt="Logo"/></a>
  <h3 align="center">A Practical Debugging Tool for Training Deep Neural Networks</h3>

  <p align="center">
    A better status screen for deep learning.
  </p>
</p>

<p align="center">
  <a href="#installation">Installation</a> •
  <a href="https://h1j9d3q.github.io/cockpit/">Docs</a> •
  <a href="experiments/">Experiments</a> •
</p>

---

```bash
pip install 'git+https://github.com/h1j9d3q/cockpit.git'
```

---

**Cockpit is a visual and statistical debugger specifically designed for deep learning.** Training a deep neural network is often a pain! Successfully training such a network usually requires either years of intuition or expensive parameter searches involving lots of trial and error. Traditional debuggers provide only limited help: They can find *syntactical errors* but not *training bugs* such as ill-chosen learning rates. **Cockpit** offers a closer, more meaningful look into the training process with multiple well-chosen *instruments*.

---

![CockpitAnimation](docs/source/_static/showcase.gif)

<!-- Installation -->
## Installation

To install **Cockpit** simply run

```bash
pip install 'git+https://github.com/h1j9d3q/cockpit'
```

If you want to run all experiments and tests, we provided a `conda` environment, with the `.conda_env.yml` file.

<!-- Documentation -->
## Documentation

The [documentation](https://h1j9d3q.github.io/cockpit/) provides a full tutorial on how to get started using **Cockpit** as well as a detailed documentation of its API.

<!-- Experiments -->
## Experiments

To showcase the capabilities of **Cockpit** we performed several experiments illustrating the usefulness of our debugging tool. The code for all experiments, as well as the generated data is presented in [experiments](experiments/). For a discussion of those experiments please refer to our paper.
