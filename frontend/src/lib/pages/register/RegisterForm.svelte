<script lang="ts">
  import { Capacitor } from "@capacitor/core";
  import Form from "$lib/ui/form/Form.svelte";
  import UsernameField from "$lib/ui/form/UsernameField.svelte";
  import EmailField from "$lib/ui/form/EmailField.svelte";
  import PasswordField from "$lib/ui/form/PasswordField.svelte";
  import ConfirmPasswordField from "$lib/ui/form/ConfirmPasswordField.svelte";
  import ServerUrlField from "$lib/ui/form/ServerUrlField.svelte";
  import Button from "$lib/ui/Button.svelte";
  import { api } from "$lib/api/index";
  import { authStore } from "$lib/stores/auth";
  import { serverUrlStore, normalizeServerUrl } from "$lib/stores/serverUrl";
  import { authView } from "$lib/app";

  const isNative = Capacitor.isNativePlatform();

  let username: string = "";
  let email: string = "";
  let password: string = "";
  let confirmPassword: string = "";
  let errorMessage: string = "";
  let isLoading: boolean = false;

  const handleSubmit = async () => {
    errorMessage = "";

    // Validation
    if (isNative && !normalizeServerUrl($serverUrlStore)) {
      errorMessage = "Server URL is required";
      return;
    }

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
    } catch (error: any) {
      errorMessage = error.message || "Registration failed";
    } finally {
      isLoading = false;
    }
  };
</script>

<Form title="Register" {errorMessage} submitHandler={handleSubmit}>
  {#if isNative}
    <ServerUrlField bind:value={$serverUrlStore} />
  {/if}
  <UsernameField bind:value={username} />
  <EmailField bind:value={email} />
  <PasswordField bind:value={password} />
  <ConfirmPasswordField bind:value={confirmPassword} />
  <Button type="submit" disabled={isLoading}>{isLoading ? "Registering..." : "Register"}</Button>
  <p class="login-link">
    Already have an account?
    <button type="button" class="link-button" onclick={() => authView.set("login")}>
      Login
    </button>
  </p>
</Form>

<style>
  .login-link {
    text-align: center;
    margin-top: 1rem;
    font-size: 0.9rem;
  }

  .link-button {
    background: none;
    border: none;
    padding: 0;
    font: inherit;
    color: var(--color-primary);
    text-decoration: underline;
    cursor: pointer;
  }
</style>
