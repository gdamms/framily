<script lang="ts">
  import { goto } from "$app/navigation";
  import Form from "$lib/components/Form.svelte";
  import UsernameField from "$lib/components/UsernameField.svelte";
  import EmailField from "$lib/components/EmailField.svelte";
  import PasswordField from "$lib/components/PasswordField.svelte";
  import ConfirmPasswordField from "$lib/components/ConfirmPasswordField.svelte";
  import RegisterButton from "$lib/components/RegisterButton.svelte";
  import { api } from "$lib/api";
  import { authStore } from "$lib/stores/auth";

  let username: string = "";
  let email: string = "";
  let password: string = "";
  let confirmPassword: string = "";
  let errorMessage: string = "";
  let isLoading: boolean = false;

  const handleSubmit = async () => {
    errorMessage = "";

    // Validation
    if (!username || !email || !password || !confirmPassword) {
      errorMessage = "All fields are required";
      return;
    }

    if (password !== confirmPassword) {
      errorMessage = "Passwords do not match";
      return;
    }

    if (password.length < 8) {
      errorMessage = "Password must be at least 8 characters";
      return;
    }

    if (username.length < 3 || username.length > 32) {
      errorMessage = "Username must be 3-32 characters";
      return;
    }

    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      errorMessage = "Username can only contain letters, numbers, and underscores";
      return;
    }

    isLoading = true;

    try {
      const response = await api.auth.register(username, email, password);
      await authStore.setToken(response.token);
      await goto("/");
    } catch (error: any) {
      errorMessage = error.message || "Registration failed";
    } finally {
      isLoading = false;
    }
  };
</script>

<Form title="Register" {errorMessage} submitHandler={handleSubmit}>
  <UsernameField bind:value={username} />
  <EmailField bind:value={email} />
  <PasswordField bind:value={password} />
  <ConfirmPasswordField bind:value={confirmPassword} />
  <RegisterButton />
  <p class="login-link">Already have an account? <a href="/login">Login</a></p>
</Form>

<style>
  .login-link {
    text-align: center;
    margin-top: 1rem;
    font-size: 0.9rem;
  }
</style>
