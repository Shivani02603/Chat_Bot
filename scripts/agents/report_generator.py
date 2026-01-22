"""
Report Generator - PDF Reports with Charts
Creates comparison reports for properties
"""

import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime


class ReportGenerator:
    """Generates PDF reports with property comparisons"""

    def __init__(self):
        # Determine project root (go up from scripts/agents/ to root)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(current_dir, '..', '..')
        self.output_dir = os.path.join(project_root, 'reports')
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_report(self, properties: list, report_type: str = 'comparison') -> str:
        """
        Generate PDF report

        Args:
            properties: List of property dictionaries
            report_type: 'comparison' or 'summary'

        Returns:
            Path to generated PDF file
        """

        if not properties:
            return None

        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.output_dir}/property_report_{timestamp}.pdf"

        # Create PDF
        with PdfPages(filename) as pdf:
            # Page 1: Price Comparison
            self._create_price_chart(properties)
            pdf.savefig()
            plt.close()

            # Page 2: Size Comparison
            self._create_size_chart(properties)
            pdf.savefig()
            plt.close()

            # Page 3: Property Details Table
            self._create_details_page(properties)
            pdf.savefig()
            plt.close()

        print(f"Report generated: {filename}")
        return filename

    def _create_price_chart(self, properties: list):
        """Create price comparison bar chart"""

        fig, ax = plt.subplots(figsize=(10, 6))

        property_ids = [p['property_id'] for p in properties]
        prices = [p['price'] / 100000 for p in properties]  # Convert to lakhs

        ax.barh(property_ids, prices, color='skyblue')
        ax.set_xlabel('Price (Lakhs)', fontsize=12)
        ax.set_title('Property Price Comparison', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

    def _create_size_chart(self, properties: list):
        """Create size comparison chart"""

        fig, ax = plt.subplots(figsize=(10, 6))

        property_ids = [p['property_id'] for p in properties]
        sizes = [p.get('property_size_sqft', 0) for p in properties]

        ax.barh(property_ids, sizes, color='lightgreen')
        ax.set_xlabel('Size (sqft)', fontsize=12)
        ax.set_title('Property Size Comparison', fontsize=14, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

    def _create_details_page(self, properties: list):
        """Create property details table"""

        fig, ax = plt.subplots(figsize=(11, 8))
        ax.axis('tight')
        ax.axis('off')

        # Prepare table data
        headers = ['Property ID', 'Location', 'Price (Lakhs)', 'Rooms', 'Size (sqft)']
        table_data = []

        for prop in properties:
            table_data.append([
                prop['property_id'],
                prop.get('location', 'N/A')[:20],  # Truncate long names
                f"{prop['price'] / 100000:.2f}",
                prop.get('num_rooms', 'N/A'),
                prop.get('property_size_sqft', 'N/A')
            ])

        # Create table
        table = ax.table(
            cellText=table_data,
            colLabels=headers,
            cellLoc='left',
            loc='center',
            colWidths=[0.15, 0.25, 0.15, 0.1, 0.15]
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)

        # Style header
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')

        plt.title('Property Details', fontsize=16, fontweight='bold', pad=20)
