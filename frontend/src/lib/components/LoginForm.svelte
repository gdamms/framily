<script lang="ts">
  import { goto } from '$app/navigation';
  import Form from "$lib/components/Form.svelte";
  import UsernameField from "$lib/components/UsernameField.svelte";
  import PasswordField from "$lib/components/PasswordField.svelte";
  import LoginButton from "$lib/components/LoginButton.svelte";
  import { api } from "$lib/api";
  import { authStore } from "$lib/stores/auth";

  let username: string = "";
  let password: string = "";
  let errorMessage: string = "";
  let isLoading: boolean = false;

  const handleSubmit = async () => {
    errorMessage = "";

    // Validation
    if (!username || !password) {
      errorMessage = "Username/email and password are required";
      return;
    }

    isLoading = true;

    try {
      const response = await api.auth.login(username, password);
      await authStore.setToken(response.token);
      await goto("/");
    } catch (error: any) {
      errorMessage = error.message || "Login failed";
    } finally {
      isLoading = false;
    }
  };
</script>

<Form title="Login" {errorMessage} submitHandler={handleSubmit}>
  <UsernameField bind:value={username} placeholder="Username or email" />
  <PasswordField bind:value={password} />
  <LoginButton />
  <p class="register-link">Don't have an account? <a href="/register">Register</a></p>
</Form>

<style>
  .register-link {
    text-align: center;
    margin-top: 1rem;
    font-size: 0.9rem;
  }
</style>
