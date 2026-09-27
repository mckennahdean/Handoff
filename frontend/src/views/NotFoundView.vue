<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import pet01 from '../assets/pets/pet_01.jpg'
import pet02 from '../assets/pets/pet_02.jpg'
import pet03 from '../assets/pets/pet_03.jpg'
import pet04 from '../assets/pets/pet_04.jpg'
import pet05 from '../assets/pets/pet_05.jpg'
import pet06 from '../assets/pets/pet_06.jpg'
import pet07 from '../assets/pets/pet_07.jpg'
import pet08 from '../assets/pets/pet_08.jpg'
import pet09 from '../assets/pets/pet_09.jpg'
import pet10 from '../assets/pets/pet_10.jpg'
import pet11 from '../assets/pets/pet_11.jpg'
import pet12 from '../assets/pets/pet_12.jpg'
import pet13 from '../assets/pets/pet_13.jpg'
import pet14 from '../assets/pets/pet_14.jpg'
import pet15 from '../assets/pets/pet_15.jpg'
import pet16 from '../assets/pets/pet_16.jpg'
import pet17 from '../assets/pets/pet_17.jpg'
import pet18 from '../assets/pets/pet_18.jpg'
import pet19 from '../assets/pets/pet_19.jpg'
import pet20 from '../assets/pets/pet_20.jpg'
import pet21 from '../assets/pets/pet_21.jpg'
import pet22 from '../assets/pets/pet_22.jpg'
import pet23 from '../assets/pets/pet_23.jpg'
import pet24 from '../assets/pets/pet_24.jpg'
import pet25 from '../assets/pets/pet_25.jpg'

const router = useRouter()

const pets = [
  pet01,
  pet02,
  pet03,
  pet04,
  pet05,
  pet06,
  pet07,
  pet08,
  pet09,
  pet10,
  pet11,
  pet12,
  pet13,
  pet14,
  pet15,
  pet16,
  pet17,
  pet18,
  pet19,
  pet20,
  pet21,
  pet22,
  pet23,
  pet24,
  pet25
]

// Select one pet when the 404 page is loaded.
const selectedPet = computed(() => {
  const index = Math.floor(Math.random() * pets.length)
  return pets[index]
})

// Return to the login page.
const goToLogin = () => {
  router.push('/login')
}

// Return to the previous page.
const goBack = () => {
  window.history.back()
}
</script>

<template>
  <main class="not-found">
    <section class="not-found-card">
      <p class="error-code">404</p>

      <h1>Oops! This page wandered off.</h1>

      <p class="message">
        We couldn't find the page you're looking for, but one of our pets
        is here to keep you company.
      </p>

      <img
        :src="selectedPet"
        alt="Handoff team pet"
        class="pet-photo"
      />

      <div class="actions">
        <button type="button" class="primary-button" @click="goToLogin">
          Go to Login
        </button>

        <button type="button" class="secondary-button" @click="goBack">
          Go Back
        </button>
      </div>
    </section>
  </main>
</template>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: #f7f3ec;
}

.not-found-card {
  width: min(700px, 100%);
  padding: 45px;
  text-align: center;
  background: #fffdf9;
  border: 1px solid #ded8ce;
  border-radius: 16px;
  box-shadow: 0 8px 30px rgba(48, 42, 34, 0.08);
}

.error-code {
  margin: 0;
  color: #d26f3d;
  font-size: 5rem;
  font-weight: 700;
  line-height: 1;
}

h1 {
  margin: 20px 0 12px;
  color: #275b4f;
  font-size: 2rem;
}

.message {
  max-width: 520px;
  margin: 0 auto 28px;
  color: #5f5a52;
  font-size: 1rem;
  line-height: 1.6;
}

.pet-photo {
  width: 280px;
  height: 280px;
  object-fit: cover;
  border-radius: 14px;
  border: 4px solid #fff;
  box-shadow: 0 6px 20px rgba(48, 42, 34, 0.12);
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 30px;
}

.primary-button,
.secondary-button {
  padding: 11px 20px;
  border-radius: 8px;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

.primary-button {
  border: 1px solid #275b4f;
  background: #275b4f;
  color: white;
}

.secondary-button {
  border: 1px solid #d26f3d;
  background: transparent;
  color: #d26f3d;
}

.primary-button:hover,
.secondary-button:hover {
  opacity: 0.9;
}

@media (max-width: 600px) {
  .not-found-card {
    padding: 30px 20px;
  }

  .error-code {
    font-size: 4rem;
  }

  h1 {
    font-size: 1.6rem;
  }

  .pet-photo {
    width: 230px;
    height: 230px;
  }

  .actions {
    flex-direction: column;
  }
}
</style>
