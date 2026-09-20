"""
Proteus JOCKY Forensic Runtime - Operation Dispatcher
"""

import json
import time
from typing import Dict, Any, Union, List, Optional

try:
    from runtime.errors import StructuredError, ErrorCode, CollectorException
    from runtime.models import OperationResult, ExecutionResult
    from runtime.registry import OperationRegistry, create_default_registry
    from compiler.ir.model import IRDocument, IROperation
except ImportError:
    try:
        from errors import StructuredError, ErrorCode, CollectorException
        from models import OperationResult, ExecutionResult
        from registry import OperationRegistry, create_default_registry
        from compiler.ir.model import IRDocument, IROperation
    except ImportError:
        # Fallback if compiler is in sys.path or standalone
        from errors import StructuredError, ErrorCode, CollectorException
        from models import OperationResult, ExecutionResult
        from registry import OperationRegistry, create_default_registry
        IRDocument = None
        IROperation = None


class OperationDispatcher:
    """
    Dispatcher that securely executes approved JOCKY IR operations through the OperationRegistry.
    Guarantees sequential execution, resilient error handling, and strict allowlisting.
    """

    def __init__(self, registry: Optional[OperationRegistry] = None):
        self.registry = registry if registry is not None else create_default_registry()

    def dispatch_operation(self, op: Union[Any, Dict[str, Any]]) -> OperationResult:
        """
        Dispatches a single IR operation to its registered collector and returns an OperationResult.
        
        :param op: An IROperation instance or a dictionary representing an operation.
        :return: OperationResult containing status, data, or structured error.
        """
        # Extract operation fields
        if hasattr(op, "id") and hasattr(op, "type") and hasattr(op, "parameters"):
            op_id = op.id
            op_type = op.type
            params = op.parameters or {}
        elif isinstance(op, dict):
            op_id = op.get("id") or op.get("operation_id", "op-000")
            op_type = op.get("type", "")
            params = op.get("parameters") or {}
        else:
            return OperationResult(
                operation_id="op-000",
                type="unknown",
                status="error",
                data=None,
                error=StructuredError(
                    code=ErrorCode.COLLECTION_FAILED,
                    message=f"Invalid operation format: {type(op)}"
                )
            )

        # Check if operation is in the allowlist / registry
        if not self.registry.is_approved(op_type):
            return OperationResult(
                operation_id=op_id,
                type=op_type,
                status="error",
                data=None,
                error=StructuredError(
                    code=ErrorCode.UNKNOWN_OPERATION,
                    message=f"Operation '{op_type}' is not recognized or permitted."
                )
            )

        collector = self.registry.get(op_type)
        if collector is None:
            return OperationResult(
                operation_id=op_id,
                type=op_type,
                status="error",
                data=None,
                error=StructuredError(
                    code=ErrorCode.NOT_IMPLEMENTED,
                    message=f"No collector registered for operation '{op_type}'."
                )
            )

        # Invoke collector with isolated error handling and timing
        t0 = time.perf_counter()
        try:
            data = collector.collect(params)
            duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return OperationResult(
                operation_id=op_id,
                type=op_type,
                status="success",
                data=data if data is not None else {},
                error=None,
                duration_ms=duration_ms
            )
        except CollectorException as ce:
            duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return OperationResult(
                operation_id=op_id,
                type=op_type,
                status="error",
                data=None,
                error=ce.to_structured_error(),
                duration_ms=duration_ms
            )
        except Exception as ex:
            duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            return OperationResult(
                operation_id=op_id,
                type=op_type,
                status="error",
                data=None,
                error=StructuredError(
                    code=ErrorCode.COLLECTION_FAILED,
                    message=str(ex) or "Collection failed unexpectedly"
                ),
                duration_ms=duration_ms
            )


    def dispatch(self, ir_input: Union[Any, Dict[str, Any], str]) -> ExecutionResult:
        """
        Executes all operations in a JOCKY IR Document in strict sequential order.
        
        :param ir_input: An IRDocument instance, a dictionary, or a JSON string.
        :return: ExecutionResult containing the ordered list of OperationResults.
        """
        # Normalize IR Document
        if isinstance(ir_input, str):
            try:
                ir_data = json.loads(ir_input)
            except json.JSONDecodeError as e:
                return ExecutionResult(
                    investigation="Unknown",
                    version="1.0",
                    results=[
                        OperationResult(
                            operation_id="op-000",
                            type="parse_error",
                            status="error",
                            data=None,
                            error=StructuredError(
                                code=ErrorCode.COLLECTION_FAILED,
                                message=f"Failed to decode IR JSON: {e}"
                            )
                        )
                    ]
                )
        elif isinstance(ir_input, dict):
            ir_data = ir_input
        elif hasattr(ir_input, "to_dict"):
            ir_data = ir_input.to_dict()
        else:
            raise TypeError(f"Unsupported IR input type: {type(ir_input)}")

        investigation = ir_data.get("investigation") or ir_data.get("name", "Investigation")
        version = ir_data.get("version", "1.0")
        operations = ir_data.get("operations", [])

        results: List[OperationResult] = []
        for op in operations:
            result = self.dispatch_operation(op)
            results.append(result)

        return ExecutionResult(
            investigation=investigation,
            version=version,
            results=results
        )
