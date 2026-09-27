package main

import (
	"context"
	"strings"
	"testing"
)

func TestExecuteJOCKYContextDoesNotRunRawSourceAsShell(t *testing.T) {
	source := `analysis "Jocky Main" {
    system.info();
}`

	got := executeJOCKYContext(context.Background(), source)
	if !strings.HasPrefix(got, "error: raw JOCKY source was not compiled") {
		t.Fatalf("expected raw JOCKY to be rejected, got %q", got)
	}
}
