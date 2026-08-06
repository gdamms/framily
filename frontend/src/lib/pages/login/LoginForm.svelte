<script lang="ts">
  import Form from "$lib/ui/form/Form.svelte";
  import UsernameField from "$lib/ui/form/UsernameField.svelte";
  import PasswordField from "$lib/ui/form/PasswordField.svelte";
  import Button from "$lib/ui/Button.svelte";
  import { api } from "$lib/api/index";
  import { authStore } from "$lib/stores/auth";
  import { authView } from "$lib/app";

  let username: string = "";
  let password: string = "";
  let rememberMe: boolean = true;
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
      const response = await api.auth.login(username, password, rememberMe);
      await authStore.setToken(response.token, rememberMe);
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
  <label class="remember-me">
    <input type="checkbox" bind:checked={rememberMe} />
    Stay logged in
  </label>
  <Button type="submit" disabled={isLoading}>{isLoading ? "Logging in..." : "Login"}</Button>
  <p class="register-link">
    Don't have an account?
    <button type="button" class="link-button" onclick={() => authView.set("register")}>
      Register
    </button>
  </p>
</Form>

<style>
  .remember-me {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    cursor: pointer;
  }

  .register-link {
    text-align: center;
    margin-top: 1rem;
    font-size: 0.9rem;
  }

  .link-button {
    background: none;
    border: none;
    padding: 0;
    font: inherit;
    color: #4593e7;
    text-decoration: underline;
    cursor: pointer;
  }
</style>
