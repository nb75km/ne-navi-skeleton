import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "../../lib/api";
import { useAuth } from "../../contexts/AuthContext";
import { Link, useNavigate } from "react-router-dom";
import {
  EyeIcon,
  EyeSlashIcon,
  LockClosedIcon,
  EnvelopeIcon,
} from "@heroicons/react/24/outline";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});
type Form = z.infer<typeof schema>;

export default function Login() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Form>({ resolver: zodResolver(schema) });

  const [showPwd, setShowPwd] = useState(false);
  const [serverErr, setServerErr] = useState("");
  const auth = useAuth();
  const nav = useNavigate();

  const onSubmit = async (data: Form) => {
  /* CookieTransport 用に x-www-form-urlencoded で送信 */
  const form = new URLSearchParams();
  form.append("username", data.email);   // ← フィールド名は username
  form.append("password", data.password);

  await api.post("/auth/jwt/login", form);
  await auth.reload();      // /users/me を叩いて user を取得
  nav("/");                 // ダッシュボードへ
};

  return (
    <div className="min-h-screen grid place-items-center bg-gradient-to-bl from-indigo-50 to-cyan-50 px-4">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-xl">
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-800">
          Sign in to NE Navi
        </h1>

        {serverErr && (
          <p className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {serverErr}
          </p>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          {/* Email */}
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Email address
            </label>
            <div className="relative mt-1">
              <EnvelopeIcon className="pointer-events-none absolute inset-y-0 left-0 ml-3 h-5 w-5 text-gray-400" />
              <input
                id="email"
                type="email"
                autoComplete="email"
                {...register("email")}
                aria-invalid={!!errors.email}
                className={`block w-full rounded-md border ${
                  errors.email ? "border-red-500" : "border-gray-300"
                } bg-white py-2 pl-10 pr-3 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200`}
                placeholder="you@example.com"
              />
            </div>
            {errors.email && (
              <p className="mt-1 text-xs text-red-600">
                {errors.email.message}
              </p>
            )}
          </div>

          {/* Password */}
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </label>
            <div className="relative mt-1">
              <LockClosedIcon className="pointer-events-none absolute inset-y-0 left-0 ml-3 h-5 w-5 text-gray-400" />
              <input
                id="password"
                type={showPwd ? "text" : "password"}
                autoComplete="current-password"
                {...register("password")}
                aria-invalid={!!errors.password}
                className={`block w-full rounded-md border ${
                  errors.password ? "border-red-500" : "border-gray-300"
                } bg-white py-2 pl-10 pr-10 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200`}
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                className="absolute inset-y-0 right-0 mr-3 flex items-center text-gray-400 hover:text-gray-600"
              >
                {showPwd ? (
                  <EyeSlashIcon className="h-5 w-5" />
                ) : (
                  <EyeIcon className="h-5 w-5" />
                )}
              </button>
            </div>
            {errors.password && (
              <p className="mt-1 text-xs text-red-600">
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-md bg-indigo-600 py-2 font-medium text-white transition-colors hover:bg-indigo-700 disabled:opacity-60"
          >
            {isSubmitting ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-600">
          Don’t have an account?{" "}
          <Link
            to="/auth/register"
            className="font-medium text-indigo-600 hover:underline"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
