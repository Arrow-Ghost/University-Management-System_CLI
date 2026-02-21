"""
Export utilities for generating PDF and Excel reports.
"""

import os
from typing import List
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class ExportError(Exception):
    """Custom exception for export errors."""
    pass


def export_to_pdf(atr_data: List[dict], output_path: str = "atr_report.pdf") -> str:
    """
    Export Action Taken Report to PDF format.
    
    Args:
        atr_data: List of dictionaries containing ATR data
        output_path: Output file path
        
    Returns:
        Path to generated PDF file
        
    Raises:
        ExportError: If export fails or reportlab is not available
    """
    if not REPORTLAB_AVAILABLE:
        raise ExportError(
            "reportlab library is not installed. "
            "Install it using: pip install reportlab"
        )
    
    if not atr_data:
        raise ExportError("No data to export.")
    
    try:
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a237e'),
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#283593'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        title = Paragraph("Action Taken Report (ATR)", title_style)
        story.append(title)
        story.append(Spacer(1, 0.2 * inch))
        
        # Report generation date
        date_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(date_text, styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Process each ATR entry
        for idx, entry in enumerate(atr_data, 1):
            # Entry header
            entry_title = f"Entry {idx}: {entry['course_code']} - {entry['course_title']}"
            story.append(Paragraph(entry_title, heading_style))
            
            # Create data table
            data = [
                ['Field', 'Value'],
                ['Course Code', entry['course_code']],
                ['Course Title', entry['course_title']],
                ['Faculty Name', entry['faculty_name']],
                ['Student Name', entry['student_name']],
                ['Registration Number', entry['student_reg_no']],
                ['Feedback Text', entry['feedback_text']],
                ['Expectations', entry['expectations'] or 'N/A'],
                ['Rating', str(entry['rating']) if entry['rating'] else 'N/A'],
                ['HOD Comments', entry['hod_comments'] or 'N/A'],
                ['Faculty Response', entry['faculty_response'] or 'N/A'],
                ['Action Taken', entry['action_taken'] or 'N/A'],
                ['Submission Date', entry['submission_date']],
                ['Action Date', entry['action_date'] or 'N/A']
            ]
            
            table = Table(data, colWidths=[2 * inch, 4 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3949ab')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(table)
            story.append(Spacer(1, 0.3 * inch))
        
        # Build PDF
        doc.build(story)
        
        return os.path.abspath(output_path)
    
    except Exception as e:
        raise ExportError(f"Error generating PDF: {str(e)}")


def export_to_excel(atr_data: List[dict], output_path: str = "atr_report.xlsx") -> str:
    """
    Export Action Taken Report to Excel format.
    
    Args:
        atr_data: List of dictionaries containing ATR data
        output_path: Output file path
        
    Returns:
        Path to generated Excel file
        
    Raises:
        ExportError: If export fails or pandas/openpyxl is not available
    """
    if not PANDAS_AVAILABLE:
        raise ExportError(
            "pandas library is not installed. "
            "Install it using: pip install pandas openpyxl"
        )
    
    if not atr_data:
        raise ExportError("No data to export.")
    
    try:
        # Prepare data for DataFrame
        df_data = []
        for entry in atr_data:
            df_data.append({
                'Course Code': entry['course_code'],
                'Course Title': entry['course_title'],
                'Faculty Name': entry['faculty_name'],
                'Student Name': entry['student_name'],
                'Registration Number': entry['student_reg_no'],
                'Feedback Text': entry['feedback_text'],
                'Expectations': entry['expectations'] or 'N/A',
                'Rating': entry['rating'] if entry['rating'] else 'N/A',
                'HOD Comments': entry['hod_comments'] or 'N/A',
                'Faculty Response': entry['faculty_response'] or 'N/A',
                'Action Taken': entry['action_taken'] or 'N/A',
                'Submission Date': entry['submission_date'],
                'Action Date': entry['action_date'] or 'N/A'
            })
        
        # Create DataFrame
        df = pd.DataFrame(df_data)
        
        # Export to Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='ATR Report', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['ATR Report']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)
        
        return os.path.abspath(output_path)
    
    except ImportError:
        raise ExportError(
            "openpyxl library is not installed. "
            "Install it using: pip install openpyxl"
        )
    except Exception as e:
        raise ExportError(f"Error generating Excel file: {str(e)}")


def display_atr_console(atr_data: List[dict]) -> None:
    """
    Display Action Taken Report in console format.
    
    Args:
        atr_data: List of dictionaries containing ATR data
    """
    if not atr_data:
        print("\nNo ATR data available.")
        return
    
    print("\n" + "=" * 80)
    print("ACTION TAKEN REPORT (ATR)")
    print("=" * 80)
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    for idx, entry in enumerate(atr_data, 1):
        print(f"\n{'─' * 80}")
        print(f"ENTRY {idx}")
        print(f"{'─' * 80}")
        print(f"Course Code          : {entry['course_code']}")
        print(f"Course Title         : {entry['course_title']}")
        print(f"Faculty Name         : {entry['faculty_name']}")
        print(f"Student Name         : {entry['student_name']}")
        print(f"Registration Number  : {entry['student_reg_no']}")
        print(f"\nFeedback Text:")
        print(f"  {entry['feedback_text']}")
        print(f"\nExpectations:")
        print(f"  {entry['expectations'] or 'N/A'}")
        print(f"\nRating               : {entry['rating'] if entry['rating'] else 'N/A'}")
        print(f"\nHOD Comments:")
        print(f"  {entry['hod_comments'] or 'N/A'}")
        print(f"\nFaculty Response:")
        print(f"  {entry['faculty_response'] or 'N/A'}")
        print(f"\nAction Taken:")
        print(f"  {entry['action_taken'] or 'N/A'}")
        print(f"\nSubmission Date      : {entry['submission_date']}")
        print(f"Action Date          : {entry['action_date'] or 'N/A'}")
        print(f"{'─' * 80}")
    
    print(f"\nTotal Entries: {len(atr_data)}")
    print("=" * 80)
