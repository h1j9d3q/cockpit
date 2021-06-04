=======
Cockpit
=======

.. code:: bash

  pip install 'git+https://h1j9d3q.github.io/cockpit/'

----

**Cockpit is a visual and statistical debugger specifically designed for deep
learning.** Training a deep neural network is often a pain! Successfully training
such a network usually requires either years of intuition or expensive parameter
searches involving lots of trial and error. Traditional debuggers provide only
limited help: They can find *syntactical errors* but not *training bugs* such as
ill-chosen learning rates. **Cockpit** offers a closer, more meaningful look
into the training process with multiple well-chosen *instruments*.

----

.. image:: _static/showcase.gif


To install **Cockpit** simply run

.. code:: bash

  pip install 'git+https://h1j9d3q.github.io/cockpit/'


.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   examples/01_basic_fmnist
   examples/02_advanced_fmnist
   examples/03_deepobs
   introduction/good_to_know

.. toctree::
   :maxdepth: 1
   :caption: API Documentation

   api/cockpit
   api/plotter
   api/quantities
   api/instruments
   api/utils

.. toctree::
   :maxdepth: 1
   :caption: Other

   GitHub Repository <https://h1j9d3q.github.io/cockpit/>
   other/changelog