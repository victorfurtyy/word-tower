<script lang="ts" setup>

</script>

<template>
  <div class="box">
    <div class="box-content">
      <p class="letter">A</p>
    </div>
  </div>
</template>

<style scopedyle>
@font-face {
  font-family: 'Tomo Bossa Black';
  src: url('@/assets/fonts/tomo_bossa_black.woff') format('woff');
}

.box {
  --box-size: 8dvw;
  --box-radius: 1.2rem;
  --scale-box: calc(100% + 0.04 * var(--box-size));

  display: flex;
  justify-content: center;
  align-items: center;
  width: var(--box-size);
  height: var(--box-size);
  border-radius: var(--box-radius);
  background-color: #FFB107;
  border: 12px solid #96550B;
  container-type: inline-size;
  box-shadow: 0 10px 0 0 #96550B;

  .box-content {
    display: flex;
    justify-content: center;
    align-items: center;
    box-sizing: border-box;
    width: var(--scale-box);
    height: var(--scale-box);
    aspect-ratio: 1;
    border: 6px solid #FED31E;
    border-radius: var(--box-radius);
  }

  .letter {
    font-family: "Tomo Bossa Black";
    font-size: 100cqw;
    margin: 0;
    line-height: 1;
    vertical-align: center;
  }
}
</style>
