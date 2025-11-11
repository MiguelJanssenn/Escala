"""
Test script for new features: chronological ordering and round-based selection
"""
import pandas as pd
from datetime import datetime

def test_chronological_sorting():
    """Test that activities are sorted chronologically"""
    print("\n=== Testing Chronological Sorting ===")
    
    # Create sample data
    df = pd.DataFrame({
        'Tipo': ['Plantão', 'Ambulatório', 'Enfermaria', 'Plantão'],
        'Data': ['2025-12-15', '2025-12-01', '2025-12-10', '2025-12-05'],
        'Horário': ['19:00-07:00', '08:00-12:00', '13:00-18:00', '07:00-19:00'],
        'Vagas': [2, 1, 1, 2],
        'Participantes': ['', '', '', '']
    })
    
    print("\nOriginal order:")
    print(df[['Tipo', 'Data', 'Horário']])
    
    # Sort chronologically
    df['data_sort'] = pd.to_datetime(df['Data'])
    df['horario_sort'] = df['Horário'].str.split('-').str[0].str.strip()
    df_sorted = df.sort_values(['data_sort', 'horario_sort'])
    df_sorted = df_sorted.drop(['data_sort', 'horario_sort'], axis=1)
    
    print("\nChronologically sorted:")
    print(df_sorted[['Tipo', 'Data', 'Horário']])
    
    # Verify order
    dates = pd.to_datetime(df_sorted['Data'].tolist())
    assert dates.is_monotonic_increasing, "Dates should be in ascending order"
    
    print("✅ Chronological sorting test passed!")
    return True

def test_bulk_activity_structure():
    """Test the structure for bulk activity addition"""
    print("\n=== Testing Bulk Activity Structure ===")
    
    # Simulate what the data editor would produce
    df_new_activities = pd.DataFrame({
        'Tipo': ['Plantão', 'Ambulatório', 'Enfermaria'],
        'Data': ['2025-12-01', '2025-12-02', '2025-12-03'],
        'Horário': ['07:00-19:00', '08:00-12:00', '13:00-18:00'],
        'Vagas': [2, 1, 1]
    })
    
    print("\nSample data editor input:")
    print(df_new_activities)
    
    # Convert to expected format
    df_to_save = df_new_activities.copy()
    df_to_save.columns = ['tipo', 'data', 'horario', 'vagas']
    
    print("\nConverted to database format:")
    print(df_to_save)
    
    # Verify structure
    assert list(df_to_save.columns) == ['tipo', 'data', 'horario', 'vagas'], "Columns should match database schema"
    assert len(df_to_save) == 3, "Should have 3 activities"
    
    print("✅ Bulk activity structure test passed!")
    return True

def test_round_order_simulation():
    """Test round order generation logic"""
    print("\n=== Testing Round Order Generation ===")
    
    import random
    
    # Simulate participants
    participants = ['user1@email.com', 'user2@email.com', 'user3@email.com', 'user4@email.com', 'user5@email.com']
    
    print(f"\nOriginal participants: {participants}")
    
    # Shuffle (as done in create_new_round)
    shuffled = participants.copy()
    random.shuffle(shuffled)
    
    print(f"Shuffled order: {shuffled}")
    
    # Create round data structure
    round_data = []
    for position, email in enumerate(shuffled, start=1):
        round_data.append({
            "escala_nome": "Test/2025",
            "numero_rodada": 1,
            "posicao": position,
            "email_participante": email,
            "ja_escolheu": False
        })
    
    df_round = pd.DataFrame(round_data)
    
    print("\nRound data structure:")
    print(df_round[['posicao', 'email_participante', 'ja_escolheu']])
    
    # Verify structure
    assert len(df_round) == len(participants), "All participants should be in the round"
    assert df_round['posicao'].tolist() == list(range(1, len(participants) + 1)), "Positions should be sequential"
    assert not df_round['ja_escolheu'].any(), "All should start with ja_escolheu=False"
    
    print("✅ Round order generation test passed!")
    return True

def test_available_slots_logic():
    """Test logic for calculating available slots"""
    print("\n=== Testing Available Slots Calculation ===")
    
    # Sample activities
    df_atividades = pd.DataFrame({
        'id_atividade': ['act1', 'act2', 'act3'],
        'escala_nome': ['Dez/2025', 'Dez/2025', 'Dez/2025'],
        'tipo': ['Plantão', 'Ambulatório', 'Enfermaria'],
        'data': ['2025-12-01', '2025-12-02', '2025-12-03'],
        'horario': ['07:00-19:00', '08:00-12:00', '13:00-18:00'],
        'vagas': [2, 1, 1]
    })
    
    # Sample choices (2 people chose act1, 1 chose act2)
    df_escolhas = pd.DataFrame({
        'id_atividade': ['act1', 'act1', 'act2'],
        'email_participante': ['user1@email.com', 'user2@email.com', 'user3@email.com'],
        'nome_participante': ['User 1', 'User 2', 'User 3']
    })
    
    print("\nActivities:")
    print(df_atividades[['id_atividade', 'tipo', 'vagas']])
    
    print("\nChoices made:")
    print(df_escolhas[['id_atividade', 'nome_participante']])
    
    # Calculate occupied slots
    escolhas_count = df_escolhas.groupby('id_atividade').size().reset_index(name='ocupadas')
    df_result = df_atividades.merge(escolhas_count, on='id_atividade', how='left')
    df_result['ocupadas'] = df_result['ocupadas'].fillna(0).astype(int)
    df_result['vagas_disponiveis'] = df_result['vagas'] - df_result['ocupadas']
    
    print("\nAvailable slots calculation:")
    print(df_result[['id_atividade', 'tipo', 'vagas', 'ocupadas', 'vagas_disponiveis']])
    
    # Verify calculations
    assert df_result.loc[df_result['id_atividade'] == 'act1', 'vagas_disponiveis'].values[0] == 0, "act1 should have 0 slots"
    assert df_result.loc[df_result['id_atividade'] == 'act2', 'vagas_disponiveis'].values[0] == 0, "act2 should have 0 slots"
    assert df_result.loc[df_result['id_atividade'] == 'act3', 'vagas_disponiveis'].values[0] == 1, "act3 should have 1 slot"
    
    # Filter only available
    df_available = df_result[df_result['vagas_disponiveis'] > 0]
    print(f"\nActivities with available slots: {len(df_available)}")
    assert len(df_available) == 1, "Only act3 should be available"
    
    print("✅ Available slots calculation test passed!")
    return True

def run_all_tests():
    """Run all tests"""
    print("Starting feature tests...\n")
    
    tests = [
        test_chronological_sorting,
        test_bulk_activity_structure,
        test_round_order_simulation,
        test_available_slots_logic
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    if all(results):
        print("✅ All feature tests passed successfully!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
