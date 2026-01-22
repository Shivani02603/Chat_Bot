"""
Renovation Estimator - Cost Calculation
Estimates renovation costs based on property size and rooms
"""


class RenovationEstimator:
    """Calculates renovation cost estimates"""

    def __init__(self):
        # Cost per sqft for different renovation types (in INR)
        self.rates = {
            'basic': 500,      # Basic painting, minor repairs
            'moderate': 1200,  # Flooring, electrical, plumbing
            'premium': 2500    # Complete makeover, modular kitchen
        }

    def estimate(self, property_size_sqft: int = None, num_rooms: int = None) -> dict:
        """
        Estimate renovation costs

        Args:
            property_size_sqft: Property size in square feet
            num_rooms: Number of rooms (if size not available)

        Returns:
            Dictionary with cost estimates
        """

        # Estimate size if not provided
        if property_size_sqft is None and num_rooms:
            property_size_sqft = self._estimate_size(num_rooms)

        if property_size_sqft is None:
            return {"error": "Need property size or number of rooms"}

        # Calculate costs
        costs = {
            'property_size_sqft': property_size_sqft,
            'basic': {
                'total': property_size_sqft * self.rates['basic'],
                'per_sqft': self.rates['basic'],
                'description': 'Basic painting, minor repairs'
            },
            'moderate': {
                'total': property_size_sqft * self.rates['moderate'],
                'per_sqft': self.rates['moderate'],
                'description': 'Flooring, electrical, plumbing upgrades'
            },
            'premium': {
                'total': property_size_sqft * self.rates['premium'],
                'per_sqft': self.rates['premium'],
                'description': 'Complete makeover with modular fittings'
            }
        }

        return costs

    def _estimate_size(self, num_rooms: int) -> int:
        """Estimate property size from number of rooms"""
        # Rough estimates
        size_map = {
            1: 600,   # 1 BHK ~600 sqft
            2: 1000,  # 2 BHK ~1000 sqft
            3: 1400,  # 3 BHK ~1400 sqft
            4: 1800,  # 4 BHK ~1800 sqft
        }
        return size_map.get(num_rooms, num_rooms * 450)

    def format_estimate(self, costs: dict) -> str:
        """Format costs as readable text"""

        if 'error' in costs:
            return costs['error']

        output = f"Renovation Cost Estimates for {costs['property_size_sqft']} sqft:\n\n"

        for level in ['basic', 'moderate', 'premium']:
            cost_info = costs[level]
            output += f"{level.upper()}:\n"
            output += f"  Total: Rs.{cost_info['total']:,}\n"
            output += f"  Rate: Rs.{cost_info['per_sqft']}/sqft\n"
            output += f"  Includes: {cost_info['description']}\n\n"

        return output
