import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from skills.codex.tools import audit_code_impl

@pytest.mark.asyncio
async def test_audit_code_impl_bind_mount():
    """Test that audit_code_impl handles bind mount paths correctly."""
    
    # Mock dependencies
    with patch('app.core.dependencies.get_code_executor') as mock_get_executor:
        mock_executor = MagicMock()
        mock_executor.run_code.return_value = {
            "exit_code": 0,
            "output": "✅ **Analysis complete!**\n\nSummary...\n\n📂 *Full report saved to: /workspace/docs/code_audit_test.md*"
        }
        mock_get_executor.return_value = mock_executor
        
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=mock_executor.run_code.return_value)
            
            with patch('os.path.exists') as mock_exists:
                # Simulate file existing on host (bind mount success)
                mock_exists.return_value = True
                
                with patch('app.services.telegram_service.telegram_service') as mock_tg:
                    mock_tg.send_message = AsyncMock()
                    mock_tg.send_document = AsyncMock()
                    
                    # Run implementation
                    result = await audit_code_impl()
                    
                    # Verify Telegram was called with correct host path
                    # /workspace/docs/... -> /current/dir/docs/...
                    assert mock_tg.send_document.call_count == 1
                    call_args = mock_tg.send_document.call_args
                    # args[0] is path, kwargs['caption'] is caption
                    assert "docs/code_audit_test.md" in call_args[0][0]
                    assert call_args[1].get('caption') == "Självanalys Rapport"

if __name__ == "__main__":
    # Manually run if executed directly
    import asyncio
    asyncio.run(test_audit_code_impl_bind_mount())
    print("Test passed!")
