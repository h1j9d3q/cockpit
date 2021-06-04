"""Histograms of individual gradient transformations."""

import torch
from backpack.extensions import BatchGrad

from cockpit.quantities.bin_adaptation import NoAdaptation
from cockpit.quantities.quantity import SingleStepQuantity
from cockpit.quantities.utils_hists import histogram2d_opt
from cockpit.quantities.utils_transforms import BatchGradTransformsHook


class GradHist1d(SingleStepQuantity):
    """Quantity class for one-dimensional histograms of indivdual gradient elements.

    The histograms consider individual gradient elements, with outliers being
    clipped to lie in the visible range.
    """

    def __init__(
        self,
        track_schedule,
        verbose=False,
        bins=100,
        range=(-2, 2),
        adapt=None,
    ):
        """Initialization sets the tracking schedule & creates the output dict.

        Args:
            track_schedule (callable): Function that maps the ``global_step``
                to a boolean, which determines if the quantity should be computed.
            verbose (bool, optional): Turns on verbose mode. Defaults to ``False``.
            bins (int): Number of bins
            range ([float, float], optional): Lower and upper limit of the bin range.
                Default: ``(-2, 2)``.
            adapt (BinAdaptation): Policy for adapting the bin limits. Per default,
                no adaptation is performed.
        """
        super().__init__(track_schedule, verbose=verbose)

        self._range = range
        self._bins = bins
        self._adapt = NoAdaptation(verbose=verbose) if adapt is None else adapt

    def extensions(self, global_step):
        """Return list of BackPACK extensions required for the computation.

        Args:
            global_step (int): The current iteration number.

        Returns:
            list: (Potentially empty) list with required BackPACK quantities.
        """
        ext = []

        if self.should_compute(global_step):
            ext.append(BatchGrad())

        ext += self._adapt.extensions(global_step)

        return ext

    def extension_hooks(self, global_step):
        """Return list of BackPACK extension hooks required for the computation.

        Args:
            global_step (int): The current iteration number.

        Returns:
            [callable]: List of required BackPACK extension hooks for the current
                iteration.
        """
        hooks = []

        if self.should_compute(global_step):
            hooks.append(
                BatchGradTransformsHook(transforms={"hist_1d": self._compute_histogram})
            )

        hooks += self._adapt.extension_hooks(global_step)

        return hooks

    def track(self, global_step, params, batch_loss):
        """Perform scheduled computations and store result.

        Args:
            global_step (int): The current iteration number.
            params ([torch.Tensor]): List of torch.Tensors holding the network's
                parameters.
            batch_loss (torch.Tensor): Mini-batch loss from current step.
        """
        super().track(global_step, params, batch_loss)

        # update limits
        if self._adapt.should_compute(global_step):
            self._range = self._adapt.compute(
                global_step, params, batch_loss, self._range
            )

    def _compute(self, global_step, params, batch_loss):
        """Evaluate the individual gradient histogram.

        Args:
            global_step (int): The current iteration number.
            params ([torch.Tensor]): List of torch.Tensors holding the network's
                parameters.
            batch_loss (torch.Tensor): Mini-batch loss from current step.

        Returns:
            dict: Entry ``'hist'`` holds the histogram, entry ``'edges'`` holds
                the bin limits.
        """
        hist = sum(p.grad_batch_transforms["hist_1d"][0] for p in params).detach()
        edges = params[0].grad_batch_transforms["hist_1d"][1]

        return {"hist": hist, "edges": edges}

    def _compute_histogram(self, batch_grad):
        """Transform individual gradients into histogram data.

        This function is be applied onto every parameter's individual gradient
        during backpropagation. If `p` denotes the parameter, then the return
        value is stored in the `"hist"` field of `p.grad_batch_transforms`.

        Args:
            batch_grad (torch.Tensor): Individual gradient of a parameter `p`. If
                `p` is of shape `(*)`, the individual gradients have shape `(N, *)`,
                where `N` denotes the batch size.

        Returns:
            (torch.Tensor, torch.Tensor): First tensor represents histogram counts,
                second tensor are bin edges. Both are on the input's device.
        """
        # NOTE ``batch_grad`` is 1/B ∇ℓᵢ so we need to compensate the 1/B.
        # Rescale histogram limits instead of tensor to save memory
        B = batch_grad.shape[0]

        start, end = self._range
        start_scaled, end_scaled = start / B, end / B
        clamped = torch.clamp(batch_grad, start_scaled, end_scaled)

        hist = torch.histc(clamped, bins=self._bins, min=start_scaled, max=end_scaled)
        edges = torch.linspace(start, end, self._bins + 1, device=batch_grad.device)

        return hist, edges


class GradHist2d(SingleStepQuantity):
    """Quantity class for two-dimensional histograms over gradient and parameters.

    Tracks two-dimensional histogram of individual gradient elements over
    parameters. Individual gradient values are binned on the x-axis, parameter
    values are binned on the y-axis.
    """

    def __init__(
        self,
        track_schedule,
        verbose=False,
        bins=(40, 50),
        range=((-1, 1), (-2, 2)),
        adapt=(None, None),
        keep_individual=False,
    ):
        """Initialize the 2D Histogram of individual gradient elements over parameters.

        Args:
            track_schedule (callable): Function that maps the ``global_step``
                to a boolean, which determines if the quantity should be computed.
            verbose (bool, optional): Turns on verbose mode. Defaults to ``False``.
            bins ([int, int]): Number of bins in x and y direction. Default:
                ``(40, 50)``
            range ([[float, float], [float, float]], optional): Bin limits in x and
                y direction. Default ``((-1, 1), (-2, 2))``.
            adapt ([BinAdaptation or None, BinAdaptation or None], optional): Policy
                for adapting the bin limits in x and y direction. ``None`` indicates
                no adaptation. Default value: ``(None, None)``.
            keep_individual (bool, optional):  Whether to keep individual
                parameter histograms. Defaults to False.
        """
        super().__init__(track_schedule, verbose=verbose)

        self._range = list(range)
        self._bins = bins
        self._adapt = [NoAdaptation(verbose=verbose) if a is None else a for a in adapt]
        self._keep_individual = keep_individual

    def extensions(self, global_step):
        """Return list of BackPACK extensions required for the computation.

        Args:
            global_step (int): The current iteration number.

        Returns:
            list: (Potentially empty) list with required BackPACK quantities.
        """
        ext = []

        if self.should_compute(global_step):
            ext.append(BatchGrad())

        for adapt in self._adapt:
            ext += adapt.extensions(global_step)

        return ext

    def extension_hooks(self, global_step):
        """Return list of BackPACK extension hooks required for the computation.

        Args:
            global_step (int): The current iteration number.

        Returns:
            [callable]: List of required BackPACK extension hooks for the current
                iteration.
        """
        hooks = []

        if self.should_compute(global_step):
            hooks.append(BatchGradTransformsHook({"hist_2d": self._compute_histogram}))

        for adapt in self._adapt:
            hooks += adapt.extension_hooks(global_step)

        return hooks

    def track(self, global_step, params, batch_loss):
        """Perform scheduled computations and store result.

        Args:
            global_step (int): The current iteration number.
            params ([torch.Tensor]): List of torch.Tensors holding the network's
                parameters.
            batch_loss (torch.Tensor): Mini-batch loss from current step.
        """
        super().track(global_step, params, batch_loss)

        # update limits
        for dim, adapt in enumerate(self._adapt):
            if adapt.should_compute(global_step):
                self._range[dim] = adapt.compute(
                    global_step, params, batch_loss, self._range
                )

    def _compute(self, global_step, params, batch_loss):
        """Aggregate histogram data over parameters and save to output."""
        hist = sum(p.grad_batch_transforms["hist_2d"][0] for p in params).detach()
        edges = params[0].grad_batch_transforms["hist_2d"][1]

        result = {"hist": hist, "edges": edges}

        if self._keep_individual:
            result["param_groups"] = len(params)

            for idx, p in enumerate(params):
                hist, edges = p.grad_batch_transforms["hist_2d"]
                hist = hist.detach()
                result[f"param_{idx}"] = {"hist": hist, "edges": edges}

        return result

    def _compute_histogram(self, batch_grad):
        """Transform individual gradients and parameters into a 2d histogram.

        Args:
            batch_grad (torch.Tensor): Individual gradient of a parameter `p`. If
                `p` is of shape `(*)`, the individual gradients have shape `(N, *)`,
                where `N` denotes the batch size.

        Returns:
            (torch.Tensor, (torch.Tensor, torch.Tensor)): First tensor represents
                histogram counts, second tuple holds the bin edges in x and y
                direction. All are on the input's device.
        """
        # NOTE ``batch_grad`` is 1/B ∇ℓᵢ so we need to compensate the 1/B
        # Rescale histogram limits instead of tensor to save memory
        B = batch_grad.shape[0]
        range = []

        # gradient axis
        dim = 0
        lower, upper = [limit / B for limit in self._range[dim]]
        range.append([lower, upper])
        bins = self._bins[dim]
        # Histogram implementation does not include the limits, clip to bin center
        bin_size = (upper - lower) / bins
        batch_grad_clamped = torch.clamp(
            batch_grad, min=lower + bin_size / 2, max=upper - bin_size / 2
        )

        # parameter axis
        dim = 1
        lower, upper = self._range[dim]
        range.append([lower, upper])
        bins = self._bins[dim]
        # Histogram implementation does not include the limits, clip to bin center
        bin_size = (upper - lower) / bins
        param_clamped = torch.clamp(
            batch_grad._param_weakref().data,
            min=lower + bin_size / 2,
            max=upper - bin_size / 2,
        )

        # chunk computation to reduce histogram memory consumption (casts to long)
        max_size = int(1e8)
        num_chunks = int(batch_grad.numel() // max_size) + 1

        hist = None

        for bg_clamped in batch_grad_clamped.chunk(num_chunks):
            chunk_hist, (edge_x, edge_y) = self.__hist_low_mem(
                bg_clamped, param_clamped, bins=self._bins, range=range
            )
            hist = chunk_hist if hist is None else hist + chunk_hist

        edge_x *= B

        return hist, (edge_x, edge_y)

    def __hist_low_mem(self, batch_grad, param, bins, range):
        """Compute histogram with memory-efficient strategy.

        Args:
            batch_grad (torch.Tensor): Individual gradients computed by BackPACK.
            param (torch.Tensor): Parameter, clipped to the histogram range.
            bins ([int, int]): Number of bins in x and y direction.
            range ([[float, float], [float, float]]): Bin limits in x and
                y direction.

        Returns:
            (torch.Tensor, (torch.Tensor, torch.Tensor)): First tensor represents
                histogram counts, second tuple holds the bin edges in x and y
                direction. All are on the input's device.
        """
        return histogram2d_opt(batch_grad, param, bins=bins, range=range)
