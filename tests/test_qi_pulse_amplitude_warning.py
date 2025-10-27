"""Test low amplitude warning functionality in QiPulse."""

import warnings

import pytest

from qiclib.code.qi_pulse import QiPulse
from qiclib.packages.constants import CONTROLLER_AMPLITUDE_MAX_VALUE


def test_low_amplitude_triggers_warning():
    """Test that amplitude below threshold triggers warning."""
    min_amplitude = 1.0 / CONTROLLER_AMPLITUDE_MAX_VALUE
    low_amplitude = min_amplitude * 0.5  # Half the minimum

    pulse = QiPulse(length=1e-6, amplitude=low_amplitude)

    with pytest.warns(
        UserWarning, match="below the minimum representable value.*will vanish"
    ):
        pulse(1e9)  # 1 GHz sample rate


def test_zero_amplitude_triggers_warning():
    """Test that zero amplitude triggers warning."""
    pulse = QiPulse(length=1e-6, amplitude=0.0)

    with pytest.warns(UserWarning, match="below the minimum representable value"):
        pulse(1e9)


def test_amplitude_above_threshold_no_warning():
    """Test that amplitude above threshold does not trigger warning."""
    min_amplitude = 1.0 / CONTROLLER_AMPLITUDE_MAX_VALUE
    high_amplitude = min_amplitude * 2.0  # Double the minimum

    pulse = QiPulse(length=1e-6, amplitude=high_amplitude)

    with warnings.catch_warnings():
        warnings.simplefilter(
            "error"
        )  # Turn warnings into errors to catch any unexpected ones
        pulse(1e9)  # Should not raise


def test_normal_amplitude_no_warning():
    """Test that normal amplitude does not trigger warning."""
    pulse = QiPulse(length=1e-6, amplitude=0.5)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pulse(1e9)  # Should not raise


def test_empty_envelope_no_warning():
    """Test that empty envelope (very short pulse) does not trigger amplitude warning."""
    # This should trigger the existing short pulse warning, not the amplitude warning
    pulse = QiPulse(length=1e-12, amplitude=0.5)  # Very short pulse

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        envelope = pulse(1e9)

        # Should have empty envelope and existing short pulse warning
        assert len(envelope) == 0
        # May have short pulse warning, but not amplitude warning
        for warning in w:
            assert "below the minimum representable value" not in str(warning.message)


def test_off_pulse_no_warning():
    """Test that an 'off' pulse does not trigger a warning"""
    pulse = QiPulse.off()  # Very short pulse

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        pulse(1e9)  # Should not raise
