import math
from time import time

class ExpDecayRateEstimator:
    """
    Estimate the time-varying rate of events via exponentially-decaying counts.

    lambda(t) = sum_j alpha * exp( -alpha * (t - t_j) )

    Parameters
    ----------
    alpha : float
        Decay rate parameter.  1/alpha is the characteristic memory length.
    """

    def __init__(self, alpha):
        self.alpha = alpha
        self.last_timestamp = None
        self.lam = 0.0

    def update(self, timestamp, count=1):
        """
        Update the rate estimate with 'count' new events at time 'timestamp'.
        Normally count=1 or 0.

        Parameters
        ----------
        timestamp : float
            Event time in seconds (must be >= previous timestamp).
        count : int
            Number of events observed at this timestamp.
        """
        if self.last_timestamp is None:
            # No prior information – simply record the first time
            self.last_timestamp = timestamp

        # Decay the current estimate up to this time
        dt = timestamp - self.last_timestamp
        if dt < 0:
            print("Warning: negative time difference; resetting last_timestamp.")
            self.last_timestamp = timestamp
            dt = 0

        self.lam *= math.exp(-self.alpha * dt)

        # Add new events
        self.lam += self.alpha * count

        self.last_timestamp = timestamp

    def get_rate(self, timestamp):
        """
        Get the estimated rate at the specified time *without* adding any new events.
        (Equivalent to "let it decay up to now".)

        Parameters
        ----------
        timestamp : float
            Time at which to evaluate the rate.
        """
        if self.last_timestamp is None:
            return 0.0

        dt = timestamp - self.last_timestamp
        if dt < 0:
            print(f"Warning: dt = {dt} < 0 -- setting dt = 0.")
            dt = 0
            #raise ValueError("Timestamps must be non-decreasing")

        return self.lam * math.exp(-self.alpha * dt)

def _demo():
    """
    Simple demonstration:
      Events at t = 0, 5, 6, 20.
      We inspect the estimated rate at various points.
    """
    alpha = 0.1
    estimator = ExpDecayRateEstimator(alpha)

    data = [
        (0.0, 1),
        (5.0, 1),
        (6.0, 1),
        (20.0, 1)
    ]

    for t, c in data:
        estimator.update(t, c)
        print(f"After update at t={t}: rate={estimator.get_rate(t):.4f}")

    # check the rate at a few later times
    for t in [21, 25, 35]:
        r = estimator.get_rate(t)
        print(f"Rate at t={t}: {r:.4f}")

if __name__ == "__main__":
    _demo()
