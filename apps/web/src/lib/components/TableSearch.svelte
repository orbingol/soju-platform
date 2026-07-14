<script lang="ts">
  interface Props {
    value?: string;
    placeholder?: string;
    onchange?: (value: string) => void;
  }

  let { value = $bindable(''), placeholder = 'Search Korean or English…', onchange }: Props = $props();

  function handleInput(event: Event) {
    const target = event.target as HTMLInputElement;
    value = target.value;
    onchange?.(value);
  }
</script>

<div class="table-search">
  <label class="table-search__label" for="vocab-search">Search</label>
  <input id="vocab-search" type="search" class="table-search__input" {placeholder} {value} oninput={handleInput} aria-label="Search vocabulary" />
</div>
