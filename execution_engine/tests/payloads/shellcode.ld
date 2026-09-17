ENTRY(shell_entry)

SECTIONS
{
    . = 0;

    .text : SUBALIGN(16) {
        *(.text.shell_entry)
        *(.text.shell_body)
        *(.text*)
    }

    .rdata : SUBALIGN(16) {
        *(.rdata)
        *(.rdata.*)
        *(.rodata)
        *(.rodata.*)
    }

    .data : SUBALIGN(16) {
        *(.data)
        *(.data.*)
    }

    /DISCARD/ : {
        *(.comment)
        *(.note*)
        *(.eh_frame*)
        *(.debug*)
        *(.pdata)
        *(.xdata)
        *(.reloc*)
    }
}
