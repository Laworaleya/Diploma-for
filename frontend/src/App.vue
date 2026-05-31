<template>
  <div class="app-wrapper">
    <AppHeader v-if="showHeader" />
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <BottomNav />
    <Toast position="top-right" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Toast from 'primevue/toast'
import AppHeader from './components/common/AppHeader.vue'
import BottomNav from './components/common/BottomNav.vue'

const route = useRoute()

const showHeader = computed(() => !['login', 'register'].includes(route.name))
</script>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-main {
  flex: 1;
}

@media (max-width: 768px) {
  .app-main {
    padding-bottom: 64px;
  }
}
</style>
