<script lang="ts">
  import { m } from "$lib/i18n.svelte";
  import Form from "$lib/ui/form/Form.svelte";
  import UsernameField from "$lib/ui/form/UsernameField.svelte";
  import PasswordField from "$lib/ui/form/PasswordField.svelte";
  import Button from "$lib/ui/Button.svelte";
  import { api } from "$lib/api/index";
  import { authStore } from "$lib/stores/auth";
  import { authView } from "$lib/app";
  import { onMount } from "svelte";

  let username: string = "";
  let password: string = "";
  let rememberMe: boolean = true;
  let errorMessage: string = "";
  let isLoading: boolean = false;
  // Only offered when the server has SMTP configured.
  let passwordResetEnabled: boolean = false;

  onMount(async () => {
    try {
      passwordResetEnabled = (await api.auth.features()).password_reset;
    } catch {
      passwordResetEnabled = false;
    }
  });

  const handleSubmit = async () => {
    errorMessage = "";

    // Validation
    if (!username || !password) {
      errorMessage = m.login_missing_fields();
      return;
    }

    isLoading = true;

    try {
      const response = await api.auth.login(username, password, rememberMe);
      await authStore.setToken(response.token, rememberMe);
    } catch (error: any) {
      errorMessage = error.message || m.login_failed();
    } finally {
      isLoading = false;
    }
  };
</script>

<Form title={m.login_title()} {errorMessage} submitHandler={handleSubmit}>
  <UsernameField bind:value={username} placeholder={m.login_username_or_email()} />
  <PasswordField bind:value={password} />
  <div class="options">
    <label class="remember-me">
      <input type="checkbox" bind:checked={rememberMe} />
      {m.login_stay_logged_in()}
    </label>
    {#if passwordResetEnabled}
      <button type="button" class="link-button" onclick={() => authView.set("forgot-password")}>
        {m.login_forgot_password()}
      </button>
    {/if}
  </div>
  <Button type="submit" disabled={isLoading}>{isLoading ? m.login_submitting() : m.login_submit()}</Button>
  <p class="register-link">
    {m.login_no_account()}
    <button type="button" class="link-button" onclick={() => authView.set("register")}>
      {m.login_register_link()}
    </button>
  </p>
</Form>

<style>
  .options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.5rem;
    font-size: 0.9rem;
  }

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
    color: var(--color-primary);
    text-decoration: underline;
    cursor: pointer;
  }
</style>
