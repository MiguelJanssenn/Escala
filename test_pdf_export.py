"""
Test script for PDF export functionality
Tests that the PDF export returns bytes (not bytearray) for Streamlit compatibility
"""
import pandas as pd
from fpdf import FPDF
import io


def dataframe_to_pdf(df):
    """Copy of the fixed function from app.py"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Cabeçalhos - ajusta larguras dinamicamente baseado no número de colunas
    num_cols = len(df.columns)
    if num_cols == 6:
        # Com Observações: Tipo, Data, Horário, Vagas, Participantes, Observações
        col_widths = [25, 20, 25, 12, 60, 38]
    else:
        # Sem Observações
        col_widths = [30, 25, 30, 15, 80]
    
    for i, col in enumerate(df.columns):
        if i < len(col_widths):
            pdf.cell(col_widths[i], 10, col, 1, 0, 'C')
    pdf.ln()
    
    # Dados
    for index, row in df.iterrows():
        for i, item in enumerate(row):
            if i < len(col_widths):
                pdf.multi_cell(col_widths[i], 10, str(item), 1, 'L')
        pdf.ln()
    
    # fpdf2 returns bytearray, convert to bytes for streamlit compatibility
    return bytes(pdf.output())


def test_pdf_export_returns_bytes():
    """Test that PDF export returns bytes type (not bytearray)"""
    print("\n=== Testing PDF Export Returns Bytes ===")
    
    # Sample data with 5 columns (without Observações)
    df = pd.DataFrame({
        'Tipo': ['Plantão', 'Ambulatório', 'Enfermaria'],
        'Data': ['2025-12-01', '2025-12-02', '2025-12-03'],
        'Horário': ['07:00-19:00', '08:00-12:00', '13:00-18:00'],
        'Vagas': [2, 1, 1],
        'Participantes': ['User1, User2', 'User3', 'User4']
    })
    
    pdf_data = dataframe_to_pdf(df)
    
    print(f"Returned type: {type(pdf_data)}")
    print(f"Is bytes: {isinstance(pdf_data, bytes)}")
    print(f"Is bytearray: {isinstance(pdf_data, bytearray)}")
    print(f"Data length: {len(pdf_data)} bytes")
    
    # Assertions
    assert isinstance(pdf_data, bytes), "PDF data should be bytes type"
    assert not isinstance(pdf_data, bytearray), "PDF data should NOT be bytearray type"
    assert len(pdf_data) > 0, "PDF data should not be empty"
    
    # Verify it starts with PDF header
    assert pdf_data[:4] == b'%PDF', "PDF data should start with %PDF header"
    
    print("✅ PDF export returns bytes correctly!")
    return True


def test_pdf_export_with_observacoes():
    """Test PDF export with Observações column (6 columns)"""
    print("\n=== Testing PDF Export with Observações ===")
    
    # Sample data with 6 columns (with Observações)
    df = pd.DataFrame({
        'Tipo': ['Plantão', 'Ambulatório'],
        'Data': ['2025-12-01', '2025-12-02'],
        'Horário': ['07:00-19:00', '08:00-12:00'],
        'Vagas': [2, 1],
        'Participantes': ['User1, User2', 'User3'],
        'Observações': ['Urgente', 'Normal']
    })
    
    pdf_data = dataframe_to_pdf(df)
    
    print(f"Returned type: {type(pdf_data)}")
    print(f"Is bytes: {isinstance(pdf_data, bytes)}")
    print(f"Data length: {len(pdf_data)} bytes")
    
    # Assertions
    assert isinstance(pdf_data, bytes), "PDF data should be bytes type"
    assert len(pdf_data) > 0, "PDF data should not be empty"
    
    print("✅ PDF export with Observações works correctly!")
    return True


def test_streamlit_download_button_compatibility():
    """Test that the returned data is compatible with Streamlit's download_button"""
    print("\n=== Testing Streamlit Download Button Compatibility ===")
    
    df = pd.DataFrame({
        'Tipo': ['Plantão'],
        'Data': ['2025-12-01'],
        'Horário': ['07:00-19:00'],
        'Vagas': [2],
        'Participantes': ['User1']
    })
    
    pdf_data = dataframe_to_pdf(df)
    
    # Streamlit's download_button expects bytes or str
    # This test verifies the data type is compatible
    is_valid = isinstance(pdf_data, (bytes, str))
    
    print(f"Compatible with st.download_button: {is_valid}")
    print(f"Type is bytes or str: {is_valid}")
    
    assert is_valid, "PDF data should be compatible with st.download_button (bytes or str)"
    
    print("✅ Data is compatible with Streamlit download_button!")
    return True


def run_all_tests():
    """Run all PDF export tests"""
    print("Starting PDF export tests...\n")
    
    tests = [
        test_pdf_export_returns_bytes,
        test_pdf_export_with_observacoes,
        test_streamlit_download_button_compatibility
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "="*60)
    if all(results):
        print("✅ All PDF export tests passed successfully!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
